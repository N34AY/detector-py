#!/usr/bin/env python3
"""
Core Motion Detection System
Clean, modular implementation of motion detection with rain filtering
"""

import cv2
import numpy as np
import time
from datetime import datetime
import json
from pathlib import Path
import logging
import subprocess
import platform
import threading

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DetectorConfig:
    """Configuration class for detector settings"""
    
    def __init__(self):
        # Motion detection settings
        self.motion_threshold = 800
        self.min_contour_area = 1500
        self.max_small_contours = 50
        self.motion_smoothing_frames = 3
        
        # Background subtractor settings
        self.bg_history = 300
        self.bg_var_threshold = 100
        self.bg_detect_shadows = True
        
        # ROI settings
        self.max_rois = 4
        self.roi_config_file = 'config/rois.json'
        
        # Notification settings
        self.notification_cooldown = 2.0
        
        # System settings
        self.prevent_sleep = True
        self.sleep_prevention_interval = 30  # seconds

class SleepPrevention:
    """Cross-platform sleep prevention utility"""
    
    def __init__(self):
        self.active = False
        self.thread = None
        self.system = platform.system().lower()
        
    def start(self):
        """Start sleep prevention"""
        if self.active:
            return
            
        self.active = True
        self.thread = threading.Thread(target=self._prevent_sleep_loop, daemon=True)
        self.thread.start()
        logger.info("Sleep prevention started")
        
    def stop(self):
        """Stop sleep prevention"""
        self.active = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1)
        logger.info("Sleep prevention stopped")
        
    def _prevent_sleep_loop(self):
        """Main sleep prevention loop"""
        while self.active:
            try:
                self._keep_awake()
                time.sleep(30)  # Keep awake every 30 seconds
            except Exception as e:
                logger.warning(f"Sleep prevention error: {e}")
                time.sleep(5)
                
    def _keep_awake(self):
        """Platform-specific keep awake implementation"""
        try:
            if self.system == 'darwin':  # macOS
                # Use caffeinate to prevent sleep
                subprocess.run(['caffeinate', '-u', '-t', '1'], 
                             capture_output=True, timeout=5)
            elif self.system == 'windows':
                # Use powercfg or SetThreadExecutionState via ctypes
                import ctypes
                ES_CONTINUOUS = 0x80000000
                ES_SYSTEM_REQUIRED = 0x00000001
                ES_DISPLAY_REQUIRED = 0x00000002
                ctypes.windll.kernel32.SetThreadExecutionState(
                    ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED)
            elif self.system == 'linux':
                # Try different Linux methods
                try:
                    # Try systemd-inhibit
                    subprocess.run(['systemd-inhibit', '--what=idle:sleep', 
                                  '--who=motion-detector', '--why=Monitoring', 
                                  'sleep', '1'], capture_output=True, timeout=5)
                except:
                    # Fallback to xset for X11 systems
                    try:
                        subprocess.run(['xset', 's', 'reset'], 
                                     capture_output=True, timeout=5)
                    except:
                        # Fallback to creating activity
                        pass
        except Exception as e:
            logger.debug(f"Keep awake method failed: {e}")

class MotionDetector:
    """Clean motion detection system with rain filtering"""
    
    def __init__(self, config: DetectorConfig = None):
        self.config = config or DetectorConfig()
        
        # Initialize sleep prevention
        self.sleep_prevention = SleepPrevention() if self.config.prevent_sleep else None
        
        # Initialize background subtractor
        self.background_subtractor = cv2.createBackgroundSubtractorMOG2(
            detectShadows=self.config.bg_detect_shadows,
            history=self.config.bg_history,
            varThreshold=self.config.bg_var_threshold
        )
        
        # ROI management
        self.rois = []
        self.motion_history = {}
        
        # Detection state
        self.rain_detection_active = False
        self.last_notification_time = 0
        
        # Auto-load ROIs
        self.load_rois()
    
    def add_roi(self, x1: int, y1: int, x2: int, y2: int) -> bool:
        """Add a new ROI"""
        try:
            if len(self.rois) >= self.config.max_rois:
                logger.warning(f"Maximum ROIs ({self.config.max_rois}) reached")
                return False
            
            # Generate unique ID
            roi_id = max([roi['id'] for roi in self.rois], default=0) + 1
            
            roi = {
                'id': roi_id,
                'coords': [int(x1), int(y1), int(x2), int(y2)],
                'motion_detected': False,
                'last_motion_time': None
            }
            
            self.rois.append(roi)
            logger.info(f"Added ROI {roi_id}: ({x1},{y1}) to ({x2},{y2})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add ROI: {e}")
            return False
    
    def delete_roi(self, roi_id: int) -> bool:
        """Delete ROI by ID"""
        try:
            for i, roi in enumerate(self.rois):
                if roi['id'] == roi_id:
                    del self.rois[i]
                    # Clean up motion history
                    self.motion_history.pop(roi_id, None)
                    logger.info(f"Deleted ROI {roi_id}")
                    return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete ROI {roi_id}: {e}")
            return False
    
    def clear_rois(self):
        """Clear all ROIs"""
        self.rois.clear()
        self.motion_history.clear()
        logger.info("All ROIs cleared")
    
    def save_rois(self, filename: str = None) -> bool:
        """Save ROIs to JSON file"""
        try:
            filename = filename or self.config.roi_config_file
            Path(filename).parent.mkdir(parents=True, exist_ok=True)
            
            with open(filename, 'w') as f:
                json.dump(self.rois, f, indent=2)
            
            logger.info(f"ROIs saved to {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save ROIs: {e}")
            return False
    
    def load_rois(self, filename: str = None) -> bool:
        """Load ROIs from JSON file"""
        try:
            filename = filename or self.config.roi_config_file
            
            if not Path(filename).exists():
                logger.info(f"No ROI config file found at {filename}")
                return False
            
            with open(filename, 'r') as f:
                self.rois = json.load(f)
            
            logger.info(f"Loaded {len(self.rois)} ROIs from {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load ROIs: {e}")
            return False
    
    def detect_motion_in_rois(self, frame: np.ndarray) -> bool:
        """Detect motion in configured ROIs with rain filtering"""
        if not self.rois:
            return False
        
        # Convert to grayscale
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if len(frame.shape) == 3 else frame
        gray_frame = cv2.GaussianBlur(gray_frame, (5, 5), 0)
        
        # Apply background subtraction
        fg_mask = self.background_subtractor.apply(gray_frame)
        
        # Enhanced morphological operations for rain filtering
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)
        
        # Detect rain pattern (many small contours)
        temp_contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        small_contours = [c for c in temp_contours if cv2.contourArea(c) < self.config.min_contour_area]
        
        # Update rain detection status
        self.rain_detection_active = len(small_contours) > self.config.max_small_contours
        
        motion_detected_any = False
        
        # Check motion in each ROI
        for roi in self.rois:
            roi_id = roi['id']
            x1, y1, x2, y2 = roi['coords']
            
            # Initialize motion history
            if roi_id not in self.motion_history:
                self.motion_history[roi_id] = []
            
            # Extract ROI from mask
            roi_mask = fg_mask[y1:y2, x1:x2]
            contours, _ = cv2.findContours(roi_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Filter significant contours
            large_contours = [c for c in contours if cv2.contourArea(c) >= self.config.min_contour_area]
            total_area = sum(cv2.contourArea(contour) for contour in large_contours)
            
            # Add to motion history
            self.motion_history[roi_id].append(total_area > self.config.motion_threshold)
            if len(self.motion_history[roi_id]) > self.config.motion_smoothing_frames:
                self.motion_history[roi_id].pop(0)
            
            # Require consistent motion over multiple frames
            consistent_motion = (
                len(self.motion_history[roi_id]) >= self.config.motion_smoothing_frames and
                sum(self.motion_history[roi_id]) >= 2  # At least 2 out of 3 frames
            )
            
            # Final motion decision (filtered during rain)
            motion_detected = consistent_motion and not self.rain_detection_active
            roi['motion_detected'] = motion_detected
            
            if motion_detected:
                motion_detected_any = True
                roi['last_motion_time'] = time.time()
                
                timestamp = datetime.now().strftime("%H:%M:%S")
                rain_status = "(Rain filtered)" if self.rain_detection_active else ""
                logger.info(f"[{timestamp}] Motion in ROI {roi_id} - Area: {total_area} {rain_status}")
        
        return motion_detected_any
    
    def process_frame(self, frame: np.ndarray) -> dict:
        """Process frame for motion detection"""
        results = {
            'motion_detected': False,
            'rain_active': self.rain_detection_active,
            'active_rois': len([roi for roi in self.rois if roi.get('motion_detected', False)])
        }
        
        # Motion detection
        if self.rois:
            results['motion_detected'] = self.detect_motion_in_rois(frame)
        
        return results
    
    def start_monitoring(self):
        """Start monitoring and sleep prevention"""
        if self.sleep_prevention:
            self.sleep_prevention.start()
            
    def stop_monitoring(self):
        """Stop monitoring and sleep prevention"""
        if self.sleep_prevention:
            self.sleep_prevention.stop()