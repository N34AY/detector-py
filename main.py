from ultralytics import YOLO
import cv2
import os
import time
import threading
from datetime import datetime
import subprocess
import signal
import atexit
import numpy as np
import logging
from pathlib import Path
import json

# Configuration Constants
CONFIDENCE_THRESHOLD = 0.25        # Adjust this value (0.1-0.9) to change detection sensitivity
MODEL_SIZE_DAY = 'yolov8n.pt'      # Fast model for day/standard cameras
MODEL_SIZE_IR = 'yolov8n.pt'       # Use nano model for IR too (better performance)
SAVE_DETECTIONS = False            # Save images when person is detected (disabled for performance)
DETECTION_LOG_FILE = 'detection_log.json'  # JSON log file
DETECTION_FOLDER = 'detections'    # Folder to save detection images
INFRARED_MODE = True               # Enable enhanced preprocessing for infrared cameras
MOTION_THRESHOLD = 200             # Minimum motion area to trigger detection (reduced for sensitivity)
MOTION_DETECTION_ENABLED = True   # Enable motion detection gating (set False to always detect)
MAX_ROIS = 4                       # Maximum number of ROIs supported

# Auto-select model based on camera mode
MODEL_SIZE = MODEL_SIZE_IR if INFRARED_MODE else MODEL_SIZE_DAY
MODEL_SIZE = MODEL_SIZE_IR if INFRARED_MODE else MODEL_SIZE_DAY
# MODEL_SIZE = 'yolov8s.pt'  # Medium speed, better accuracy
# MODEL_SIZE = 'yolov8m.pt'  # Slower, best accuracy

class PersonDetector:
    def __init__(self, model_size=MODEL_SIZE, confidence_threshold=CONFIDENCE_THRESHOLD):
        """
        Initialize the Person Detector
        
        Args:
            model_size: YOLOv8 model size ('yolov8n.pt', 'yolov8s.pt', 'yolov8m.pt', etc.)
            confidence_threshold: Minimum confidence for detection (0.0 to 1.0)
        """
        print("Loading YOLO model...")
        print(f"Selected model: {model_size} ({'IR optimized' if INFRARED_MODE else 'Standard'})")
        self.model = YOLO(model_size)
        self.confidence_threshold = confidence_threshold
        self.last_notification_time = 0
        self.notification_cooldown = 2.0  # Seconds between notifications
        self.person_detected = False
        
        # Multiple ROI (Region of Interest) variables
        self.rois = []  # List of ROI dictionaries
        self.active_roi_index = -1  # Currently selected ROI for drawing
        self.roi_start_point = None
        self.roi_end_point = None
        self.selecting_roi = False
        
        # Legacy ROI system (backward compatibility)
        self.roi_selected = False
        self.roi_coords = None
        
        # ROI selection state with timeout
        self.roi_selection_start_time = None
        
        # Motion detection variables (simplified)
        self.background_subtractor = cv2.createBackgroundSubtractorMOG2(
            detectShadows=True, 
            history=500,
            varThreshold=50
        )
        self.motion_detected_rois = set()
        self.background_learning_frames = 0
        
        # UI interaction
        self.ui_action = None  # Store UI button actions
        
        # Setup components
        self.setup_logging()
        
        # Sleep prevention
        self.caffeinate_process = None
        self._start_caffeinate()
        
        # Detection logging
        self.detection_count = 0
        self.setup_logging()
        
        # Legacy video recording variables (kept for compatibility)
        self.video_writer = None
        self.recording_start_time = None
        self.is_recording = False
        self.last_detection_time = None
        
        # Performance optimization settings
        self.model.overrides['verbose'] = False  # Reduce output
        
    def _start_caffeinate(self):
        """Start caffeinate process to prevent sleep"""
        try:
            self.caffeinate_process = subprocess.Popen(['caffeinate', '-d', '-i'])
            atexit.register(self._stop_caffeinate)
            print("✅ Sleep prevention activated")
        except Exception as e:
            print(f"⚠️ Could not start sleep prevention: {e}")
    
    def _stop_caffeinate(self):
        """Stop caffeinate process"""
        if self.caffeinate_process:
            try:
                self.caffeinate_process.terminate()
                self.caffeinate_process.wait(timeout=5)
                print("✅ Sleep prevention deactivated")
            except:
                pass
    
    def setup_logging(self):
        """Setup detection logging and create directories"""
        # Create detection folder if it doesn't exist
        self.detection_folder = Path(DETECTION_FOLDER)
        self.detection_folder.mkdir(exist_ok=True)
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('person_detection.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Load or create detection log
        self.log_file = Path(DETECTION_LOG_FILE)
        if self.log_file.exists():
            try:
                with open(self.log_file, 'r') as f:
                    self.detection_log = json.load(f)
            except:
                self.detection_log = {"detections": [], "rois": []}
        else:
            self.detection_log = {"detections": [], "rois": []}
    
    def log_detection(self, confidence, bbox):
        """Log detection to JSON file"""
        try:
            detection_entry = {
                "timestamp": datetime.now().isoformat(),
                "confidence": float(confidence),
                "bbox": [float(x) for x in bbox],
                "detection_id": self.detection_count
            }
            
            self.detection_log["detections"].append(detection_entry)
            
            # Save to file
            with open(self.log_file, 'w') as f:
                json.dump(self.detection_log, f, indent=2)
                
            self.logger.info(f"Detection logged: ID={self.detection_count}, Conf={confidence:.2f}")
            
        except Exception as e:
            self.logger.error(f"Failed to log detection: {e}")
        
    def play_notification_sound(self):
        """Play notification sound in a separate thread to avoid blocking"""
        def play_sound():
            try:
                if os.name != 'nt':  # macOS/Linux
                    os.system('afplay /System/Library/Sounds/Ping.aiff 2>/dev/null')
                else:  # Windows
                    os.system('echo \a')
            except:
                pass  # Ignore sound errors
        
        # Play sound in background thread
        sound_thread = threading.Thread(target=play_sound, daemon=True)
        sound_thread.start()
    
    def notify_motion_detected(self, roi_index):
        """Handle motion detection notification with cooldown"""
        current_time = time.time()
        
        # Only notify if enough time has passed since last notification
        if current_time - self.last_notification_time > self.notification_cooldown:
            self.detection_count += 1
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] Motion detected in ROI {roi_index}! (ID: {self.detection_count})")
            
            # Play notification sound
            self.play_notification_sound()
            
            self.last_notification_time = current_time
            
            return True  # New detection
        return False  # Cooldown period
    
    def log_motion_detection(self, roi_index):
        """Log motion detection to JSON file"""
        try:
            detection_entry = {
                "timestamp": datetime.now().isoformat(),
                "type": "motion",
                "roi_index": roi_index,
                "roi_coords": self.rois[roi_index]['coords'],
                "detection_id": self.detection_count
            }
            
            self.detection_log["detections"].append(detection_entry)
            
            # Save to file
            with open(self.log_file, 'w') as f:
                json.dump(self.detection_log, f, indent=2)
                
            self.logger.info(f"Motion logged: ROI={roi_index}, ID={self.detection_count}")
            
        except Exception as e:
            self.logger.error(f"Failed to log motion detection: {e}")
    
    def select_roi_with_opencv(self, frame):
        """Use OpenCV's ROI selection with existing ROIs visible"""
        print(f"\nSelect ROI {len(self.rois)+1}/{MAX_ROIS}:")
        print("- Click and drag to select area")
        print("- Press SPACE/ENTER to confirm")
        print("- Press ESC to cancel")
        
        # Create a frame with existing ROIs visible
        display_frame = frame.copy()
        
        # Draw existing ROIs for reference
        for roi in self.rois:
            x1, y1, x2, y2 = roi['coords']
            cv2.rectangle(display_frame, (x1, y1), (x2, y2), (100, 100, 100), 2)
            cv2.putText(display_frame, f"ROI{roi['id']}", (x1, y1-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 100, 100), 1)
        
        # Add instruction overlay
        overlay = display_frame.copy()
        cv2.rectangle(overlay, (10, 10), (400, 80), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, display_frame, 0.3, 0, display_frame)
        
        cv2.putText(display_frame, f"Select ROI {len(self.rois)+1}/{MAX_ROIS}", (20, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        cv2.putText(display_frame, "Drag to select, SPACE=confirm, ESC=cancel", (20, 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        cv2.putText(display_frame, "Gray boxes = existing ROIs", (20, 65), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
        
        # Use OpenCV's selectROI function
        roi = cv2.selectROI("Select ROI - Existing ROIs shown in gray", display_frame, 
                           showCrosshair=True, fromCenter=False)
        cv2.destroyWindow("Select ROI - Existing ROIs shown in gray")
        
        if roi[2] > 0 and roi[3] > 0:  # Valid ROI selected
            x, y, w, h = roi
            new_roi = {
                'coords': (x, y, x+w, y+h),
                'id': len(self.rois),
                'motion_detected': False
            }
            self.rois.append(new_roi)
            print(f"✅ ROI {new_roi['id']} added: {w}x{h} at ({x},{y})")
            return True
        else:
            print("❌ ROI selection cancelled")
            return False
    
    def preprocess_frame(self, frame):
        """Enhanced preprocessing for infrared cameras and monitor displays"""
        if INFRARED_MODE:
            # Enhanced preprocessing for infrared cameras
            return self.preprocess_infrared_frame(frame)
        else:
            # Standard preprocessing for regular cameras
            return self.preprocess_standard_frame(frame)
    
    def preprocess_infrared_frame(self, frame):
        """Optimized preprocessing for infrared cameras (performance focused)"""
        # Convert to grayscale if not already (infrared cameras often output grayscale)
        if len(frame.shape) == 3:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            gray = frame.copy()
        
        # 1. Light noise reduction (faster than aggressive)
        gray = cv2.medianBlur(gray, 3)  # Reduced from 5
        
        # 2. Enhanced contrast using CLAHE
        clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))  # Reduced from 3.0
        enhanced = clahe.apply(gray)
        
        # 3. Gamma correction optimized for infrared
        gamma = 0.8  # Less aggressive than 0.7
        inv_gamma = 1.0 / gamma
        table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
        enhanced = cv2.LUT(enhanced, table)
        
        # 4. Skip morphological operations for better performance
        # Skip edge enhancement for better performance
        
        # 5. Simple heat-map effect (faster)
        enhanced = cv2.applyColorMap(enhanced, cv2.COLORMAP_HOT)
        
        # 6. Skip final noise reduction for better performance
        
        return enhanced
    
    def detect_motion_in_rois(self, frame):
        """Detect motion in all ROIs with improved sensitivity"""
        self.motion_detected_rois.clear()
        
        # Convert to grayscale for better motion detection
        if len(frame.shape) == 3:
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            gray_frame = frame
        
        # Apply Gaussian blur to reduce noise
        gray_frame = cv2.GaussianBlur(gray_frame, (5, 5), 0)
        
        # Apply background subtraction
        fg_mask = self.background_subtractor.apply(gray_frame)
        
        # Clean up the mask with morphological operations
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)
        
        # Check motion in each ROI
        for i, roi in enumerate(self.rois):
            x1, y1, x2, y2 = roi['coords']
            roi_mask = fg_mask[y1:y2, x1:x2]
            
            # Count motion pixels
            motion_pixels = cv2.countNonZero(roi_mask)
            roi_area = (x2 - x1) * (y2 - y1)
            motion_percentage = (motion_pixels / roi_area) * 100 if roi_area > 0 else 0
            
            # Only count significant motion to reduce noise
            if motion_pixels > MOTION_THRESHOLD:
                self.motion_detected_rois.add(i)
                roi['motion_detected'] = True
            else:
                roi['motion_detected'] = False
        
        return fg_mask
    
    def preprocess_standard_frame(self, frame):
        """Standard preprocessing for regular cameras with monitor displays"""
        # Convert to LAB color space for better brightness adjustment
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization) to L channel
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        
        # Merge channels and convert back to BGR
        enhanced = cv2.merge([l, a, b])
        enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
        
        # Gamma correction to brighten dark areas
        gamma = 1.2  # Adjust for night mode cameras
        inv_gamma = 1.0 / gamma
        table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
        enhanced = cv2.LUT(enhanced, table)
        
        # Reduce noise for night mode cameras
        enhanced = cv2.bilateralFilter(enhanced, 9, 75, 75)
        
        return enhanced
    
    def get_roi_frame(self, frame):
        """Extract ROI from frame"""
        if self.roi_coords:
            x1, y1, x2, y2 = self.roi_coords
            roi = frame[y1:y2, x1:x2]
            return roi
        return frame
    
    def draw_detection_boxes(self, frame, result):
        """Manually draw detection boxes on the original frame"""
        if result is None or result.boxes is None:
            return frame
        
        frame_copy = frame.copy()
        
        for box in result.boxes:
            cls = int(box.cls[0])
            conf = float(box.conf[0])
            
            if cls == 0 and conf >= self.confidence_threshold:  # Person class
                # Get box coordinates
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                
                # If ROI is selected, adjust coordinates to original frame
                if self.roi_selected and self.roi_coords:
                    roi_x1, roi_y1, _, _ = self.roi_coords
                    x1 += roi_x1
                    y1 += roi_y1
                    x2 += roi_x1
                    y2 += roi_y1
                
                # Draw bounding box
                cv2.rectangle(frame_copy, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
                
                # Draw label
                label = f"Person {conf:.2f}"
                label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
                cv2.rectangle(frame_copy, (int(x1), int(y1) - label_size[1] - 10), 
                            (int(x1) + label_size[0], int(y1)), (0, 255, 0), -1)
                cv2.putText(frame_copy, label, (int(x1), int(y1) - 5), 
                          cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
        
        return frame_copy
    
    def draw_roi_rectangle(self, frame):
        """Draw existing ROIs"""
        # Draw existing ROIs
        for roi in self.rois:
            x1, y1, x2, y2 = roi['coords']
            color = (0, 0, 255) if roi.get('motion_detected', False) else (0, 255, 0)
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(frame, f"ROI{roi['id']}", (x1, y1-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
    
    def draw_ui_panel(self, frame):
        """Draw UI control panel"""
        height, width = frame.shape[:2]
        panel_height = 120
        panel_y = height - panel_height
        
        # Draw panel background
        cv2.rectangle(frame, (0, panel_y), (width, height), (40, 40, 40), -1)
        cv2.line(frame, (0, panel_y), (width, panel_y), (100, 100, 100), 2)
        
        # Button dimensions
        btn_width = 120
        btn_height = 30
        btn_spacing = 10
        start_x = 20
        
        # Add ROI button
        btn_y = panel_y + 15
        cv2.rectangle(frame, (start_x, btn_y), (start_x + btn_width, btn_y + btn_height), (0, 100, 200), -1)
        cv2.rectangle(frame, (start_x, btn_y), (start_x + btn_width, btn_y + btn_height), (255, 255, 255), 2)
        cv2.putText(frame, "Add ROI (R)", (start_x + 15, btn_y + 20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Clear ROIs button
        clear_x = start_x + btn_width + btn_spacing
        cv2.rectangle(frame, (clear_x, btn_y), (clear_x + btn_width, btn_y + btn_height), (0, 50, 150), -1)
        cv2.rectangle(frame, (clear_x, btn_y), (clear_x + btn_width, btn_y + btn_height), (255, 255, 255), 2)
        cv2.putText(frame, "Clear ROIs (C)", (clear_x + 10, btn_y + 20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Quit button
        quit_x = clear_x + btn_width + btn_spacing
        cv2.rectangle(frame, (quit_x, btn_y), (quit_x + btn_width, btn_y + btn_height), (50, 50, 150), -1)
        cv2.rectangle(frame, (quit_x, btn_y), (quit_x + btn_width, btn_y + btn_height), (255, 255, 255), 2)
        cv2.putText(frame, "Quit (Q)", (quit_x + 25, btn_y + 20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Status info
        info_y = btn_y + btn_height + 15
        status_text = f"ROIs: {len(self.rois)}/{MAX_ROIS}"
        cv2.putText(frame, status_text, (start_x, info_y), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        motion_text = "MOTION DETECTED!" if self.person_detected else "Monitoring..."
        color = (0, 100, 255) if self.person_detected else (100, 255, 100)
        cv2.putText(frame, motion_text, (start_x + 150, info_y), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 1)
        
        # Instructions
        inst_y = info_y + 25
        cv2.putText(frame, "Controls: R=Add ROI, C=Clear, Q=Quit", (start_x, inst_y), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
    
    def mouse_callback(self, event, x, y, flags, param):
        """Handle mouse clicks on UI buttons"""
        if event == cv2.EVENT_LBUTTONDOWN:
            height, width = param.shape[:2]
            panel_y = height - 120
            btn_y = panel_y + 15
            btn_height = 30
            btn_width = 120
            btn_spacing = 10
            start_x = 20
            
            # Check if click is in button area
            if btn_y <= y <= btn_y + btn_height:
                # Add ROI button
                if start_x <= x <= start_x + btn_width:
                    self.ui_action = 'add_roi'
                    return
                    
                # Clear ROIs button
                clear_x = start_x + btn_width + btn_spacing
                if clear_x <= x <= clear_x + btn_width:
                    self.ui_action = 'clear_rois'
                    return
                    
                # Quit button
                quit_x = clear_x + btn_width + btn_spacing
                if quit_x <= x <= quit_x + btn_width:
                    self.ui_action = 'quit'
                    return
    
    def mouse_callback(self, event, x, y, flags, param):
        """Handle mouse clicks on UI buttons"""
        if event == cv2.EVENT_LBUTTONDOWN:
            height, width = param.shape[:2]
            panel_y = height - 120
            btn_y = panel_y + 15
            btn_height = 30
            btn_width = 120
            btn_spacing = 10
            start_x = 20
            
            # Check if click is in button area
            if btn_y <= y <= btn_y + btn_height:
                # Add ROI button
                if start_x <= x <= start_x + btn_width:
                    self.ui_action = 'add_roi'
                    return
                    
                # Clear ROIs button
                clear_x = start_x + btn_width + btn_spacing
                if clear_x <= x <= clear_x + btn_width:
                    self.ui_action = 'clear_rois'
                    return
                    
                # Quit button
                quit_x = clear_x + btn_width + btn_spacing
                if quit_x <= x <= quit_x + btn_width:
                    self.ui_action = 'quit'
                    return
    
    def start_video_recording_old(self, frame):
        """Legacy recording method for backward compatibility"""
        if not RECORD_TRAINING_VIDEOS or getattr(self, 'is_recording', False):
            return
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"training_{timestamp}.mp4"
            filepath = self.training_folder / filename
            
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            fps = 30
            frame_size = (frame.shape[1], frame.shape[0])
            
            self.legacy_video_writer = cv2.VideoWriter(str(filepath), fourcc, fps, frame_size)
            
            if self.legacy_video_writer.isOpened():
                self.is_recording = True
                self.legacy_recording_start_time = time.time()
                print(f"Started legacy recording: {filename}")
            
        except Exception as e:
            print(f"Failed to start legacy recording: {e}")
    
    def stop_video_recording_old(self):
        """Stop legacy recording"""
        if hasattr(self, 'legacy_video_writer') and hasattr(self, 'is_recording'):
            try:
                self.legacy_video_writer.release()
                self.is_recording = False
                print("Stopped legacy recording")
            except Exception as e:
                print(f"Failed to stop legacy recording: {e}")
    
    def write_frame_to_video(self, frame):
        """Write frame to legacy video recording"""
        if hasattr(self, 'legacy_video_writer') and hasattr(self, 'is_recording') and self.is_recording:
            try:
                self.legacy_video_writer.write(frame)
            except Exception as e:
                print(f"Failed to write frame to legacy recording: {e}")
    
    def check_recording_duration(self):
        """Check if legacy recording should stop"""
        if hasattr(self, 'is_recording') and self.is_recording and hasattr(self, 'legacy_recording_start_time'):
            if time.time() - self.legacy_recording_start_time > VIDEO_RECORD_DURATION:
                self.stop_video_recording_old()
    
    def handle_detection_recording(self, person_detected):
        """Legacy detection recording handler"""
        return person_detected and RECORD_TRAINING_VIDEOS
        """Start recording a video segment for training data"""
        if not RECORD_TRAINING_VIDEOS or self.is_recording:
            return
        
        try:
            # Generate unique filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"training_{timestamp}.mp4"
            filepath = os.path.join(TRAINING_VIDEO_FOLDER, filename)
            
            # Get frame dimensions
            height, width, _ = frame.shape
            
            # Define the codec and create VideoWriter object
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            self.video_writer = cv2.VideoWriter(filepath, fourcc, 20.0, (width, height))
            
            if self.video_writer.isOpened():
                self.is_recording = True
                self.recording_start_time = time.time()
                self.logger.info(f"Started recording: {filename}")
                print(f"🎥 Recording started: {filename}")
            else:
                print(f"❌ Failed to start recording: {filename}")
                
        except Exception as e:
            print(f"❌ Error starting video recording: {e}")
    
    def write_frame_to_video(self, frame):
        """Write frame to current video recording"""
        if self.is_recording and self.video_writer and self.video_writer.isOpened():
            self.video_writer.write(frame)
    
    def stop_video_recording(self):
        """Stop current video recording"""
        if self.is_recording and self.video_writer:
            try:
                self.video_writer.release()
                self.is_recording = False
                duration = time.time() - self.recording_start_time if self.recording_start_time else 0
                print(f"🎥 Recording stopped. Duration: {duration:.1f}s")
                self.logger.info(f"Recording stopped. Duration: {duration:.1f}s")
                self.video_writer = None
                self.recording_start_time = None
            except Exception as e:
                print(f"❌ Error stopping video recording: {e}")
    
    def check_recording_duration(self):
        """Check if current recording should be stopped based on duration"""
        if (self.is_recording and self.recording_start_time and 
            time.time() - self.recording_start_time >= VIDEO_SEGMENT_DURATION):
            self.stop_video_recording()
    
    def handle_detection_recording(self, person_detected):
        """Handle video recording based on detection state"""
        if not RECORD_TRAINING_VIDEOS:
            return False
        
        current_time = time.time()
        
        if person_detected:
            self.last_detection_time = current_time
            
            # Start recording if detection-based recording is enabled and not already recording
            if RECORD_ON_DETECTION and not self.is_recording:
                return True  # Signal to start recording
        
        # Continue recording if we're in continuous mode
        if RECORD_CONTINUOUS and not self.is_recording:
            return True  # Signal to start recording
        
        # Stop recording if no recent detection and we're in detection-based mode
        if (RECORD_ON_DETECTION and self.is_recording and self.last_detection_time and 
            current_time - self.last_detection_time > 5.0):  # 5 seconds after last detection
            self.stop_video_recording()
        
        return False
    
    def draw_recording_indicator(self, frame):
        """Draw recording indicator on frame"""
        if self.is_recording:
            # Draw red circle for recording indicator
            cv2.circle(frame, (30, 30), 10, (0, 0, 255), -1)
            cv2.putText(frame, "REC", (50, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            
            # Show recording duration
            if self.recording_start_time:
                duration = time.time() - self.recording_start_time
                duration_text = f"{int(duration)}s"
                cv2.putText(frame, duration_text, (90, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
    
    def process_frame(self, frame):
        """Process frame for motion detection"""
        # Only do motion detection if we have ROIs and background has learned
        if len(self.rois) > 0:
            self.background_learning_frames += 1
            
            if self.background_learning_frames > 30:  # Allow background to learn
                self.detect_motion_in_rois(frame)
                
                # Check for motion in any ROI
                motion_detected_this_frame = False
                for i, roi in enumerate(self.rois):
                    if roi.get('motion_detected', False):
                        motion_detected_this_frame = True
                        # Avoid spam notifications
                        if not hasattr(roi, 'last_notification') or time.time() - roi.get('last_notification', 0) > 2:
                            self.notify_motion_detected(i)
                            self.log_motion_detection(i)
                            roi['last_notification'] = time.time()
                
                self.person_detected = motion_detected_this_frame
            else:
                self.person_detected = False
        else:
            self.person_detected = False
    
    def run_detection(self, source=0, display_window=True):
        """
        Run person detection on video source
        
        Args:
            source: Video source (0 for webcam, path for video file)
            display_window: Whether to show video window
        """
        print(f"🎯 Starting motion detection system...")
        print("📋 Controls:")
        print("  R - Add new ROI zone (opens selection tool)")
        print("  C - Clear all ROI zones")
        print("  Q - Quit application")
        print("💡 UI buttons are shown at bottom of video window")
        print("")
        
        # Initialize video capture
        cap = cv2.VideoCapture(source)
        
        if not cap.isOpened():
            print(f"Error: Could not open video source: {source}")
            return
        
        # Set camera properties optimized for performance
        if INFRARED_MODE:
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            cap.set(cv2.CAP_PROP_FPS, 30)
            cap.set(cv2.CAP_PROP_EXPOSURE, -8)  # Very low exposure for IR
            cap.set(cv2.CAP_PROP_BRIGHTNESS, 0.3)  # Lower brightness for IR
            cap.set(cv2.CAP_PROP_CONTRAST, 2.0)  # Higher contrast for IR
            cap.set(cv2.CAP_PROP_GAIN, 0.1)  # Minimal gain to reduce IR noise
            cap.set(cv2.CAP_PROP_GAMMA, 100)  # Adjust gamma for IR
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce buffer for better performance
        else:
            # Standard camera settings for monitor detection
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            cap.set(cv2.CAP_PROP_FPS, 30)
            cap.set(cv2.CAP_PROP_EXPOSURE, -7)
            cap.set(cv2.CAP_PROP_BRIGHTNESS, 0.4)
            cap.set(cv2.CAP_PROP_CONTRAST, 1.5)
            cap.set(cv2.CAP_PROP_SATURATION, 1.2)
            cap.set(cv2.CAP_PROP_GAIN, 0.3)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce buffer for better performance
        
        frame_count = 0
        process_every_n_frames = 5  # Regular processing frequency
        
        # Create window
        if display_window:
            cv2.namedWindow('Motion Detection')
            # Set mouse callback for UI interactions
            cv2.setMouseCallback('Motion Detection', self.mouse_callback, None)
        
        try:
            while True:
                ret, frame = cap.read()
                
                if not ret:
                    print("Failed to read frame from camera")
                    break
                
                frame_count += 1
                original_frame = frame.copy()
                annotated_frame = frame.copy()
                
                # Process motion detection
                if frame_count % process_every_n_frames == 0:
                    self.process_frame(frame)
                
                if display_window:
                    # Draw ROI rectangles
                    self.draw_roi_rectangle(annotated_frame)
                    
                    # Draw UI panel
                    self.draw_ui_panel(annotated_frame)
                    
                    # Update mouse callback with current frame
                    cv2.setMouseCallback('Motion Detection', self.mouse_callback, annotated_frame)
                    
                    # Display the frame
                    cv2.imshow('Motion Detection', annotated_frame)
                
                # Handle UI button actions
                if self.ui_action:
                    if self.ui_action == 'add_roi':
                        if len(self.rois) >= MAX_ROIS:
                            print(f"❌ Maximum {MAX_ROIS} ROIs reached. Clear existing ROIs first.")
                        else:
                            success = self.select_roi_with_opencv(original_frame)
                            if success:
                                print(f"📍 Total ROIs: {len(self.rois)}/{MAX_ROIS}")
                    elif self.ui_action == 'clear_rois':
                        if len(self.rois) > 0:
                            count = len(self.rois)
                            self.rois.clear()
                            self.motion_detected_rois.clear()
                            self.background_learning_frames = 0
                            print(f"🗑️ Cleared {count} ROIs")
                        else:
                            print("ℹ️ No ROIs to clear")
                    elif self.ui_action == 'quit':
                        print("\n👋 Quitting...")
                        break
                    
                    self.ui_action = None  # Reset action
                
                # Handle keyboard input
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    print("\n👋 Quitting...")
                    break
                elif key == ord('r'):  # Add ROI
                    if len(self.rois) >= MAX_ROIS:
                        print(f"❌ Maximum {MAX_ROIS} ROIs reached. Press 'c' to clear existing ROIs.")
                    else:
                        success = self.select_roi_with_opencv(original_frame)
                        if success:
                            print(f"📍 Total ROIs: {len(self.rois)}/{MAX_ROIS}")
                elif key == ord('c'):
                    # Clear all ROIs
                    if len(self.rois) > 0:
                        self.rois.clear()
                        self.motion_detected_rois.clear()
                        self.background_learning_frames = 0  # Reset background learning
                        print(f"🗑️  All {len(self.rois)} ROIs cleared")
                    else:
                        print("ℹ️  No ROIs to clear")
                
        except KeyboardInterrupt:
            print("\nDetection stopped by user")
        
        finally:
            # Cleanup
            cap.release()
            if display_window:
                cv2.destroyAllWindows()
            self._stop_caffeinate()  # Stop sleep prevention
            
            # Print detection summary
            print(f"\n=== Motion Detection Summary ===")
            print(f"Total motion events: {self.detection_count}")
            print(f"ROIs configured: {len(self.rois)}")
            print(f"Log file: {DETECTION_LOG_FILE}")
            print("Detection ended")

if __name__ == "__main__":
    # Initialize detector with configurable settings
    detector = PersonDetector()
    
    print("=== Monitor Detection Mode ===")
    print("Optimized for detecting people on monitor displays")
    print("Features:")
    print("- Enhanced brightness and contrast for dark/reflection areas")
    print(f"- {'INFRARED' if INFRARED_MODE else 'STANDARD'} camera preprocessing mode")
    print("- Night mode camera support with noise reduction")
    print("- Adaptive histogram equalization for better visibility")
    if INFRARED_MODE:
        print("- Specialized infrared camera enhancements:")
        print("  * Aggressive noise reduction for IR sensors")
        print("  * Heat signature simulation with color mapping")
        print("  * Morphological operations for IR artifact removal")
        print("  * Edge enhancement for better person detection")
    print("Settings:")
    print(f"- Confidence Threshold: {CONFIDENCE_THRESHOLD}")
    print(f"- Day Model: {MODEL_SIZE_DAY}")
    print(f"- IR Model: {MODEL_SIZE_IR}")
    print(f"- Active Model: {MODEL_SIZE} ({'IR optimized' if INFRARED_MODE else 'Standard'})")
    print(f"- Infrared Mode: {'ON' if INFRARED_MODE else 'OFF'}")
    print(f"- Log File: {DETECTION_LOG_FILE}")
    print("- Video Recording: DISABLED")
    print("")
    print("- Position webcam to minimize reflections")
    print("- Use ROI to focus on the video area of the monitor")
    print("- Works with both day and night mode camera feeds")
    print("- Edit CONFIDENCE_THRESHOLD constant to adjust sensitivity")
    print()
    
    # Run detection
    detector.run_detection(source=0, display_window=True)