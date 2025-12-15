#!/usr/bin/env python3
"""
Web Interface for Person Detection System
Clean Flask application with WebSocket support
"""

import json
import threading
import time
import base64
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import logging

# Import our clean detector
import sys
import os
from pathlib import Path

# Add parent directory to path to access src module
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from src.detector import MotionDetector, DetectorConfig

# Web app configuration
WEB_HOST = '0.0.0.0'
WEB_PORT = 5001
DEBUG_MODE = False

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'detector_web_secret_2025'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Global sleep prevention for web app
global_sleep_prevention = None

class WebDetector:
    """Web interface wrapper for MotionDetector"""
    
    def __init__(self):
        self.detector = None
        self.camera_active = False
        self.camera_thread = None
        self.current_frame = None
        self.stats = {
            'fps': 0,
            'camera_status': 'disconnected',
            'total_detections': 0,
            'last_detection_time': None,
            'rain_detected': False,
            'active_rois': 0,
            'motion_detected_rois': []
        }
    
    def initialize(self, camera_source: int = 0) -> bool:
        """Initialize the detection system"""
        try:
            config = DetectorConfig()
            self.detector = MotionDetector(config)
            logger.info("Detector initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize detector: {e}")
            return False
    
    def start_camera(self, source: int = 0) -> bool:
        """Start camera feed"""
        if self.camera_active:
            return True
        
        try:
            self.camera_thread = threading.Thread(
                target=self._camera_loop,
                args=(source,),
                daemon=True
            )
            self.camera_active = True
            self.camera_thread.start()
            logger.info("Camera feed started")
            return True
        except Exception as e:
            logger.error(f"Failed to start camera: {e}")
            return False
    
    def stop_camera(self):
        """Stop camera feed"""
        self.camera_active = False
        if self.camera_thread and self.camera_thread.is_alive():
            self.camera_thread.join(timeout=2)
        self.stats['camera_status'] = 'disconnected'
        logger.info("Camera feed stopped")
    
    def _camera_loop(self, source):
        """Main camera processing loop"""
        cap = cv2.VideoCapture(source)
        if not cap.isOpened():
            logger.error("Failed to open camera")
            self.camera_active = False
            return
        
        self.stats['camera_status'] = 'connected'
        fps_counter = 0
        fps_start_time = time.time()
        
        try:
            while self.camera_active:
                ret, frame = cap.read()
                if not ret:
                    logger.warning("Failed to read frame")
                    break
                
                # Process frame with detector
                if self.detector:
                    results = self.detector.process_frame(frame)
                    
                    # Update stats
                    if results['motion_detected']:
                        self.stats['total_detections'] += 1
                        self.stats['last_detection_time'] = datetime.now().isoformat()
                    
                    self.stats['rain_detected'] = results['rain_active']
                    self.stats['active_rois'] = len(self.detector.rois)
                    self.stats['motion_detected_rois'] = [
                        roi['id'] for roi in self.detector.rois 
                        if roi.get('motion_detected', False)
                    ]
                
                # Store frame for web interface (no overlay needed)
                self.current_frame = frame
                
                # Calculate FPS
                fps_counter += 1
                if fps_counter >= 30:
                    elapsed = time.time() - fps_start_time
                    self.stats['fps'] = fps_counter / elapsed if elapsed > 0 else 0
                    fps_counter = 0
                    fps_start_time = time.time()
                
                # Emit frame to web clients
                self._emit_frame()
                
                time.sleep(0.03)  # ~30 FPS
                
        except Exception as e:
            logger.error(f"Camera loop error: {e}")
        finally:
            cap.release()
            self.camera_active = False
            self.stats['camera_status'] = 'disconnected'
    
    def _emit_frame(self):
        """Emit frame to web clients"""
        try:
            if self.current_frame is not None:
                _, buffer = cv2.imencode('.jpg', self.current_frame, 
                                       [cv2.IMWRITE_JPEG_QUALITY, 85])
                frame_data = base64.b64encode(buffer).decode('utf-8')
                
                socketio.emit('frame_update', {
                    'frame': frame_data,
                    'stats': self.stats
                })
        except Exception as e:
            logger.error(f"Failed to emit frame: {e}")
    
    def get_roi_list(self) -> list:
        """Get current ROI list"""
        if not self.detector:
            return []
        
        roi_list = []
        for roi in self.detector.rois:
            x1, y1, x2, y2 = roi['coords']
            roi_info = {
                'id': roi['id'],
                'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2,
                'width': x2 - x1,
                'height': y2 - y1,
                'area': (x2 - x1) * (y2 - y1),
                'motion_detected': roi.get('motion_detected', False),
                'last_detection': roi.get('last_motion_time', None)
            }
            roi_list.append(roi_info)
        
        return roi_list

# Global web detector instance
web_detector = WebDetector()

# Routes
@app.route('/')
def index():
    """Main web interface"""
    return render_template('index.html')

@app.route('/api/initialize', methods=['POST'])
def api_initialize():
    """Initialize detection system"""
    try:
        data = request.json or {}
        camera_source = data.get('camera_source', 0)
        
        success = web_detector.initialize(camera_source)
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/camera/start', methods=['POST'])
def api_start_camera():
    """Start camera feed"""
    try:
        data = request.json or {}
        source = data.get('source', 0)
        
        success = web_detector.start_camera(source)
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/camera/stop', methods=['POST'])
def api_stop_camera():
    """Stop camera feed"""
    try:
        web_detector.stop_camera()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/camera/status')
def api_camera_status():
    """Get camera status"""
    return jsonify({
        'camera_active': web_detector.camera_active,
        'stats': web_detector.stats,
        'roi_count': len(web_detector.get_roi_list())
    })

@app.route('/api/rois')
def api_get_rois():
    """Get all ROIs"""
    return jsonify({'rois': web_detector.get_roi_list()})

@app.route('/api/rois/add', methods=['POST'])
def api_add_roi():
    """Add new ROI"""
    try:
        data = request.json
        x1, y1, x2, y2 = data['x1'], data['y1'], data['x2'], data['y2']
        
        if web_detector.detector:
            success = web_detector.detector.add_roi(x1, y1, x2, y2)
            if success:
                web_detector.detector.save_rois()  # Auto-save
            return jsonify({'success': success})
        else:
            return jsonify({'success': False, 'error': 'Detector not initialized'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/rois/delete/<int:roi_id>', methods=['DELETE'])
def api_delete_roi(roi_id):
    """Delete ROI by ID"""
    try:
        if web_detector.detector:
            success = web_detector.detector.delete_roi(roi_id)
            if success:
                web_detector.detector.save_rois()  # Auto-save
            return jsonify({'success': success})
        else:
            return jsonify({'success': False, 'error': 'Detector not initialized'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/rois/clear', methods=['POST'])
def api_clear_rois():
    """Clear all ROIs"""
    try:
        if web_detector.detector:
            web_detector.detector.clear_rois()
            web_detector.detector.save_rois()  # Auto-save
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Detector not initialized'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/config/motion', methods=['GET', 'POST'])
def api_motion_config():
    """Get or update motion detection configuration"""
    try:
        if request.method == 'POST':
            data = request.json
            if web_detector.detector:
                config = web_detector.detector.config
                
                # Update configuration
                if 'motion_threshold' in data:
                    config.motion_threshold = data['motion_threshold']
                if 'min_contour_area' in data:
                    config.min_contour_area = data['min_contour_area']
                if 'max_small_contours' in data:
                    config.max_small_contours = data['max_small_contours']
                
                return jsonify({'success': True, 'config': {
                    'motion_threshold': config.motion_threshold,
                    'min_contour_area': config.min_contour_area,
                    'max_small_contours': config.max_small_contours
                }})
            else:
                return jsonify({'success': False, 'error': 'Detector not initialized'})
        else:
            # GET request
            if web_detector.detector:
                config = web_detector.detector.config
                return jsonify({
                    'motion_threshold': config.motion_threshold,
                    'min_contour_area': config.min_contour_area,
                    'max_small_contours': config.max_small_contours
                })
            else:
                return jsonify({'success': False, 'error': 'Detector not initialized'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# WebSocket events
@socketio.on('connect')
def on_connect():
    """Client connected"""
    logger.info('Client connected')
    emit('status', {'connected': True})

@socketio.on('disconnect')
def on_disconnect():
    """Client disconnected"""
    logger.info('Client disconnected')

def start_global_sleep_prevention():
    """Start global sleep prevention for the web app"""
    global global_sleep_prevention
    try:
        # Import here to avoid circular imports
        from src.detector import SleepPrevention
        global_sleep_prevention = SleepPrevention()
        global_sleep_prevention.start()
        logger.info("Global sleep prevention started for web app")
    except Exception as e:
        logger.warning(f"Failed to start sleep prevention: {e}")

def stop_global_sleep_prevention():
    """Stop global sleep prevention"""
    global global_sleep_prevention
    if global_sleep_prevention:
        global_sleep_prevention.stop()
        logger.info("Global sleep prevention stopped")

if __name__ == '__main__':
    try:
        # Start sleep prevention when web app starts
        start_global_sleep_prevention()
        
        logger.info(f"Starting web server on {WEB_HOST}:{WEB_PORT}")
        socketio.run(app, host=WEB_HOST, port=WEB_PORT, debug=DEBUG_MODE)
    except KeyboardInterrupt:
        logger.info("Web server interrupted")
    finally:
        # Stop sleep prevention when web app stops
        stop_global_sleep_prevention()