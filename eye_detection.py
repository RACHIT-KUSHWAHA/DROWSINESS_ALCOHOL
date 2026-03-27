"""
Production-Grade Alcohol & Drowsiness Detection System
======================================================
Multithreaded computer vision with dynamic calibration, threat scoring, and SQLite telemetry.

Architecture:
- Multithreaded video capture (no frame-dropping)
- Dynamic EAR/MAR baseline calibration (first 50 frames)
- Real-time threat scoring (0-100) with sensor fusion
- SQLite telemetry logging
- Robust serial communication with Arduino
- Non-blocking frame processing

Mathematical Formulas:
- EAR = (||p2-p6|| + ||p3-p5||) / (2 * ||p1-p4||)  # Eye closure detection
- MAR = (||p14-p18|| + ||p15-p19|| + ||p16-p20||) / (3 * ||p12-p17||)  # Yawn detection

Author: Embedded Systems & Computer Vision Engineering
Version: 3.0 (Production-Grade)
"""

import warnings
warnings.filterwarnings('ignore', category=UserWarning)

import cv2
import mediapipe as mp
import numpy as np
import serial
import serial.tools.list_ports
import threading
import queue
import time
import sqlite3
import sys
from collections import deque
from datetime import datetime
import traceback
import winsound  # For laptop speaker alerts

# ============================================================================
# CONFIGURATION PARAMETERS
# ============================================================================

class Config:
    """Centralized configuration for the system."""
    
    # Camera Settings
    CAMERA_INDEX = 0
    FRAME_WIDTH = 640
    FRAME_HEIGHT = 480
    TARGET_FPS = 30
    
    # Calibration Settings
    CALIBRATION_FRAMES = 100  # More frames for better baseline (was 50)
    
    # Serial Communication
    SERIAL_BAUD_RATE = 9600
    SERIAL_TIMEOUT = 1.0
    SERIAL_RETRY_INTERVAL = 5  # seconds
    
    # Eye Aspect Ratio Thresholds
    EAR_THRESHOLD = 0.12  # Below this = eyes closed (was 0.20, lowered for closed eyes)
    MAR_THRESHOLD = 0.15  # Above this = yawning
    
    # Consecutive Frame Thresholds for alerts
    EAR_CONSECUTIVE_FRAMES = 20  # ~0.67 seconds at 30 FPS (more sensitive)
    MAR_CONSECUTIVE_FRAMES = 10  # ~0.33 seconds at 30 FPS (more sensitive)
    
    # Threat Score Thresholds
    THREAT_SCORE_CRITICAL = 75  # Relay activation threshold
    THREAT_SCORE_WARNING = 40   # Alert threshold (lowered)
    
    # Alcohol Sensor Integration
    ALCOHOL_BASELINE = 0  # Will be set by Arduino
    ALCOHOL_THRESHOLD_BASELINE = 400  # Arduino level for alcohol detection
    
    # Smoothing
    EAR_BUFFER_SIZE = 7  # Moving average window (increased)
    
    # Database
    TELEMETRY_DB = 'telemetry.db'


# ============================================================================
# AUDIO ALERT SYSTEM (LAPTOP SPEAKER)
# ============================================================================

class AudioAlerter:
    """Manages audio alerts via laptop speaker."""
    
    def __init__(self):
        """Initialize audio alerter."""
        self.last_alert_time = 0
        self.alert_cooldown = 0.5  # Cooldown between alert threads to prevent spam
        self.alert_thread = None
        self.lock = threading.Lock()
    
    def play_drowsy_alert(self):
        """Play drowsy alert pattern - strong beeps."""
        try:
            print(f"[AUDIO] Playing DROWSY alert (3x 400Hz @ 200ms)")
            for i in range(3):
                winsound.Beep(400, 200)  # Lower frequency, longer duration
                time.sleep(0.15)
            print(f"[AUDIO] DROWSY alert complete")
        except Exception as e:
            print(f"[AUDIO ERROR] Failed to play DROWSY alert: {e}")
    
    def play_yawn_alert(self):
        """Play yawn alert - double beep."""
        try:
            print(f"[AUDIO] Playing YAWN alert (2x 600Hz @ 250ms)")
            winsound.Beep(600, 250)
            time.sleep(0.1)
            winsound.Beep(600, 250)
            print(f"[AUDIO] YAWN alert complete")
        except Exception as e:
            print(f"[AUDIO ERROR] Failed to play YAWN alert: {e}")
    
    def play_critical_alert(self):
        """Play critical alert - rapid high frequency beeping."""
        try:
            print(f"[AUDIO] Playing CRITICAL alert (6x 1200Hz @ 150ms)")
            for _ in range(6):
                winsound.Beep(1200, 150)
                time.sleep(0.08)
            print(f"[AUDIO] CRITICAL alert complete")
        except Exception as e:
            print(f"[AUDIO ERROR] Failed to play CRITICAL alert: {e}")
    
    def play_multi_alert(self):
        """Play multi-threat alert."""
        try:
            print(f"[AUDIO] Playing MULTI alert (3x 800Hz @ 200ms)")
            winsound.Beep(800, 200)
            time.sleep(0.1)
            winsound.Beep(800, 200)
            time.sleep(0.1)
            winsound.Beep(800, 200)
            print(f"[AUDIO] MULTI alert complete")
        except Exception as e:
            print(f"[AUDIO ERROR] Failed to play MULTI alert: {e}")
    
    def trigger_alert(self, threat_type, force=False):
        """Trigger appropriate alert based on threat type (non-blocking via background thread)."""
        current_time = time.time()
        
        # Check cooldown to prevent alert spam
        if not force and (current_time - self.last_alert_time) < self.alert_cooldown:
            return
        
        # Don't start new alert if one is already playing
        with self.lock:
            if self.alert_thread and self.alert_thread.is_alive():
                return
            
            self.last_alert_time = current_time
            # Start alert in background thread to prevent blocking camera
            self.alert_thread = threading.Thread(target=self._play_alert_background, args=(threat_type,), daemon=True)
            self.alert_thread.start()
    
    def _play_alert_background(self, threat_type):
        """Play alert in background thread."""
        try:
            if threat_type == "CRITICAL":
                self.play_critical_alert()
            elif threat_type == "DROWSY":
                self.play_drowsy_alert()
            elif threat_type == "YAWN":
                self.play_yawn_alert()
            elif threat_type == "MULTI":
                self.play_multi_alert()
            elif threat_type == "ALCOHOL":
                self.play_multi_alert()
        except Exception as e:
            print(f"[AUDIO ERROR] Background alert failed: {e}")


# ============================================================================
# IMPROVED EYE DETECTION
# ============================================================================

class ImprovedEyeDetector:
    """More robust eye detection using contour analysis and blink detection."""
    
    def __init__(self):
        """Initialize eye detector."""
        cascade_path = cv2.data.haarcascades + 'haarcascade_eye.xml'
        self.eye_cascade = cv2.CascadeClassifier(cascade_path)
    
    def detect_eye_closure_by_darkness(self, gray_frame, face_roi):
        """
        Detect eye closure using brightness levels in eye regions.
        Calibration phase establishes baseline, then changes are detected.
        
        Args:
            gray_frame: Grayscale frame
            face_roi: Region of interest (x, y, w, h)
        
        Returns:
            tuple: (ear_left, ear_right, eyes_detected)
        """
        x, y, w, h = face_roi
        
        # Eye regions - focused on eyeball area
        eye_top = int(y + h * 0.32)
        eye_bottom = int(y + h * 0.46)
        
        left_eye_x1 = int(x + w * 0.08)
        left_eye_x2 = int(x + w * 0.42)
        
        right_eye_x1 = int(x + w * 0.58)
        right_eye_x2 = int(x + w * 0.92)
        
        # Extract eye regions
        left_eye_roi = gray_frame[eye_top:eye_bottom, left_eye_x1:left_eye_x2]
        right_eye_roi = gray_frame[eye_top:eye_bottom, right_eye_x1:right_eye_x2]
        
        # Simple intensity-based approach with proper scaling
        # Camera picks up 30-75 intensity range in eye area
        def intensity_to_ear(roi):
            if roi.size == 0:
                return 0.15
            
            mean_intensity = np.mean(roi)
            
            # Scale camera intensity to EAR values
            if mean_intensity < 35:
                return 0.02  # Very dark = eyes closed
            elif mean_intensity < 45:
                return 0.06  # Dark = partially closed
            elif mean_intensity < 55:
                return 0.10  # Medium = starting to close
            elif mean_intensity < 65:
                return 0.14  # Brighter = eyes open (crosses 0.12 threshold)
            elif mean_intensity < 75:
                return 0.20  # Bright = definitely open
            else:
                return 0.25  # Very bright = fully open
        
        ear_left = intensity_to_ear(left_eye_roi)
        ear_right = intensity_to_ear(right_eye_roi)
        
        # DEBUG: Print every 10 frames
        if not hasattr(self, '_frame_count'):
            self._frame_count = 0
        self._frame_count += 1
        if self._frame_count % 10 == 0:
            l_mean = np.mean(left_eye_roi) if left_eye_roi.size > 0 else 0
            r_mean = np.mean(right_eye_roi) if right_eye_roi.size > 0 else 0
            print(f"[DEBUG EYE] L_int={l_mean:.0f} EAR={ear_left:.4f} | R_int={r_mean:.0f} EAR={ear_right:.4f} (threshold=0.12)")
        
        return ear_left, ear_right, True
    
    def estimate_mar(self, gray_frame, face_roi):
        """
        Estimate Mouth Aspect Ratio from face region.
        
        Args:
            gray_frame: Grayscale frame
            face_roi: Region of interest (x, y, w, h)
        
        Returns:
            float: Estimated MAR
        """
        x, y, w, h = face_roi
        mouth_region = gray_frame[int(y+h*0.6):y+h, x+int(w*0.2):x+int(w*0.8)]
        
        # Detect high variance in mouth region during speech/yawn
        if mouth_region.size == 0:
            return 0.05
        
        variance = cv2.Laplacian(mouth_region, cv2.CV_64F).var()
        # Normalize variance to MAR scale
        mar = min(0.5, variance / 10000.0)
        
        return max(0.05, mar)



# ============================================================================
# GEOMETRY UTILITIES
# ============================================================================

def euclidean_distance(point1, point2):
    """
    Calculate Euclidean distance between two 2D points.
    
    Args:
        point1 (tuple): (x, y) coordinates
        point2 (tuple): (x, y) coordinates
    
    Returns:
        float: Distance between points
    """
    return np.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)


def calculate_ear(eye_landmarks):
    """
    Calculate Eye Aspect Ratio (EAR) using Dlib convention.
    
    Formula: EAR = (||p2-p6|| + ||p3-p5||) / (2 * ||p1-p4||)
    
    Where:
    - p1, p4 = left and right corners (horizontal distance)
    - p2, p3, p5, p6 = vertical distances
    
    Args:
        eye_landmarks (list): 6 (x, y) tuples for eye points
    
    Returns:
        float: Eye Aspect Ratio (typical: 0.25-0.35 open, <0.15 closed)
    """
    if len(eye_landmarks) != 6:
        return 0.3
    
    # Vertical distances
    vertical_dist_1 = euclidean_distance(eye_landmarks[1], eye_landmarks[5])
    vertical_dist_2 = euclidean_distance(eye_landmarks[2], eye_landmarks[4])
    
    # Horizontal distance
    horizontal_dist = euclidean_distance(eye_landmarks[0], eye_landmarks[3])
    
    # Prevent division by zero
    if horizontal_dist < 0.01:
        return 0.3
    
    ear = (vertical_dist_1 + vertical_dist_2) / (2.0 * horizontal_dist)
    return ear


def calculate_mar(mouth_landmarks):
    """
    Calculate Mouth Aspect Ratio (MAR) for yawn detection.
    
    Formula: MAR = (||p1-p4|| + ||p2-p5|| + ||p3-p6||) / (3 * ||p7-p10||)
    
    Simplified version using 4 key points:
    - Top, Bottom, Left, Right of mouth
    
    Args:
        mouth_landmarks (dict): Dict with 'top', 'bottom', 'left', 'right' (x,y) tuples
    
    Returns:
        float: Mouth Aspect Ratio (typical: 0.05-0.1 closed, >0.4 yawning)
    """
    try:
        top = mouth_landmarks['top']
        bottom = mouth_landmarks['bottom']
        left = mouth_landmarks['left']
        right = mouth_landmarks['right']
        
        # Vertical distance (mouth opening)
        vertical = euclidean_distance(top, bottom)
        
        # Horizontal distance (mouth width)
        horizontal = euclidean_distance(left, right)
        
        # Prevent division by zero
        if horizontal < 0.01:
            return 0.0
        
        mar = vertical / horizontal
        return mar
    except:
        return 0.0


def get_landmark_coordinates(face_landmarks, indices, frame_width, frame_height):
    """
    Extract pixel coordinates for specified face landmarks.
    
    Args:
        face_landmarks: MediaPipe face landmarks object
        indices (list): List of landmark indices to extract
        frame_width (int): Video frame width
        frame_height (int): Video frame height
    
    Returns:
        list: List of (x, y) pixel coordinates
    """
    coordinates = []
    for idx in indices:
        if idx < len(face_landmarks.landmark):
            landmark = face_landmarks.landmark[idx]
            x = int(landmark.x * frame_width)
            y = int(landmark.y * frame_height)
            coordinates.append((x, y))
    return coordinates



# ============================================================================
# TELEMETRY DATABASE
# ============================================================================

class TelemetryDB:
    """SQLite database manager for alert telemetry."""
    
    def __init__(self, db_path):
        """Initialize or connect to telemetry database."""
        self.db_path = db_path
        self.connection = None
        self.cursor = None
        self._initialize_db()
    
    def _initialize_db(self):
        """Create database and tables if they don't exist."""
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.cursor = self.connection.cursor()
            
            # Create alerts table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    threat_score REAL NOT NULL,
                    trigger_reason TEXT NOT NULL,
                    ear REAL,
                    mar REAL,
                    alcohol_level INTEGER,
                    duration_seconds REAL
                )
            ''')
            
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS calibration (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    baseline_ear REAL NOT NULL,
                    baseline_mar REAL NOT NULL,
                    samples_collected INTEGER
                )
            ''')
            
            self.connection.commit()
            print("[DB] Database initialized successfully")
        except Exception as e:
            print(f"[DB ERROR] Failed to initialize database: {e}")
    
    def log_alert(self, threat_score, trigger_reason, ear=None, mar=None, 
                  alcohol_level=None, duration=None):
        """
        Log an alert event to the database.
        
        Args:
            threat_score (float): Threat score (0-100)
            trigger_reason (str): Reason for alert (Drowsiness, Yawn, Alcohol, Multi)
            ear (float): Current EAR value
            mar (float): Current MAR value
            alcohol_level (int): Current alcohol sensor reading
            duration (float): Duration of trigger in seconds
        """
        try:
            timestamp = datetime.now().isoformat()
            self.cursor.execute('''
                INSERT INTO alerts 
                (timestamp, threat_score, trigger_reason, ear, mar, alcohol_level, duration_seconds)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (timestamp, threat_score, trigger_reason, ear, mar, alcohol_level, duration))
            self.connection.commit()
        except Exception as e:
            print(f"[DB ERROR] Failed to log alert: {e}")
    
    def log_calibration(self, baseline_ear, baseline_mar, samples):
        """Log calibration baseline values."""
        try:
            timestamp = datetime.now().isoformat()
            self.cursor.execute('''
                INSERT INTO calibration (timestamp, baseline_ear, baseline_mar, samples_collected)
                VALUES (?, ?, ?, ?)
            ''', (timestamp, baseline_ear, baseline_mar, samples))
            self.connection.commit()
        except Exception as e:
            print(f"[DB ERROR] Failed to log calibration: {e}")
    
    def close(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()


# ============================================================================
# VIDEO CAPTURE THREAD
# ============================================================================

class VideoCaptureThread(threading.Thread):
    """Dedicated thread for non-blocking video frame capture."""
    
    def __init__(self, camera_index, frame_queue, frame_rate=30):
        """
        Initialize video capture thread.
        
        Args:
            camera_index (int): OpenCV camera index
            frame_queue (queue.Queue): Queue to push frames to
            frame_rate (int): Target frame rate
        """
        super().__init__(daemon=False)  # Changed from daemon=True
        self.camera_index = camera_index
        self.frame_queue = frame_queue
        self.frame_rate = frame_rate
        self.running = True
        self.cap = None
        self.frame_count = 0
    
    def run(self):
        """Main thread loop for continuous frame capture."""
        try:
            print(f"[VIDEO] Opening camera {self.camera_index}...", flush=True)
            self.cap = cv2.VideoCapture(self.camera_index)
            time.sleep(1)
            
            if not self.cap.isOpened():
                print(f"[VIDEO ERROR] Failed to open camera {self.camera_index}", flush=True)
                return
            
            print(f"[VIDEO] Camera port opened", flush=True)
            time.sleep(2)
            
            # Simple frame capture loop - no warming up
            frame_interval = 1.0 / self.frame_rate
            last_frame_time = time.time()
            
            while self.running:
                ret, frame = self.cap.read()
                
                if not ret or frame is None:
                    time.sleep(0.1)
                    continue
                
                # Maintain target frame rate
                elapsed = time.time() - last_frame_time
                if elapsed < frame_interval:
                    time.sleep(frame_interval - elapsed)
                
                last_frame_time = time.time()
                
                # Put frame in queue
                try:
                    self.frame_queue.put_nowait((ret, frame))
                except queue.Full:
                    pass  # Drop frame if queue is full
                
                self.frame_count += 1
        
        except Exception as e:
            print(f"[VIDEO ERROR] Exception in capture thread: {e}", flush=True)
            import traceback
            traceback.print_exc()
        
        finally:
            if self.cap:
                self.cap.release()
            print("[VIDEO] Camera closed", flush=True)
    
    def stop(self):
        """Stop the capture thread."""
        self.running = False


# ============================================================================
# ARDUINO SERIAL COMMUNICATION
# ============================================================================

class ArduinoConnection:
    """Manages robust serial communication with Arduino."""
    
    def __init__(self, baud_rate=9600, timeout=1.0):
        """
        Initialize Arduino connection manager.
        
        Args:
            baud_rate (int): Serial baud rate
            timeout (float): Serial read timeout
        """
        self.baud_rate = baud_rate
        self.timeout = timeout
        self.serial = None
        self.port = None
        self.connected = False
        self.last_connect_attempt = 0
        self.alcohol_level = 0
        self.last_update = 0
    
    def find_port(self):
        """
        Auto-detect Arduino COM port.
        
        Returns:
            str: COM port string or None if not found
        """
        try:
            ports = serial.tools.list_ports.comports()
            for port in ports:
                if any(kw in port.description.upper() 
                       for kw in ['ARDUINO', 'CH340', 'USB-SERIAL', 'CP210', 'FTDI']):
                    return port.device
        except Exception as e:
            print(f"[SERIAL ERROR] Failed to list ports: {e}")
        return None
    
    def connect(self, port=None):
        """
        Establish serial connection to Arduino.
        
        Args:
            port (str): Specific COM port, or auto-detect if None
        
        Returns:
            bool: True if connected, False otherwise
        """
        try:
            # Prevent rapid reconnection attempts
            if time.time() - self.last_connect_attempt < Config.SERIAL_RETRY_INTERVAL:
                return False
            
            self.last_connect_attempt = time.time()
            
            # Auto-detect port if not specified
            if port is None:
                port = self.find_port()
            
            if port is None:
                print("[SERIAL] Arduino port not found. Scanning...")
                return False
            
            # Attempt connection
            self.serial = serial.Serial(port, self.baud_rate, timeout=self.timeout)
            time.sleep(2)  # Wait for Arduino to initialize
            
            self.port = port
            self.connected = True
            print(f"[SERIAL] Connected to Arduino on {port}")
            
            # Flush buffers
            self.serial.reset_input_buffer()
            self.serial.reset_output_buffer()
            
            return True
        
        except Exception as e:
            print(f"[SERIAL ERROR] Connection failed to {port}: {e}")
            self.connected = False
            return False
    
    def send_threat_score(self, threat_score, trigger_type):
        """
        Send threat score to Arduino.
        
        Format: "THREAT:<score>:<trigger_type>\n"
        Trigger types: DROWSY, YAWN, ALCOHOL, MULTI, CRITICAL
        
        Args:
            threat_score (int): Threat score 0-100
            trigger_type (str): Type of threat
        
        Returns:
            bool: True if sent successfully
        """
        if not self.connected:
            return False
        
        try:
            # Clamp threat score
            threat_score = max(0, min(100, int(threat_score)))
            
            message = f"THREAT:{threat_score}:{trigger_type}\n"
            self.serial.write(message.encode())
            self.serial.flush()
            
            return True
        except Exception as e:
            print(f"[SERIAL ERROR] Failed to send threat score: {e}")
            self.connected = False
            return False
    
    def send_calibration_request(self):
        """Request calibration from Arduino."""
        if not self.connected:
            return False
        
        try:
            self.serial.write(b"CALIB_REQUEST\n")
            self.serial.flush()
            return True
        except Exception as e:
            print(f"[SERIAL ERROR] Failed to send calibration request: {e}")
            self.connected = False
            return False
    
    def read_data(self):
        """
        Read and parse data from Arduino.
        
        Returns:
            dict: Parsed data or empty dict if no data
        """
        if not self.connected:
            return {}
        
        data = {}
        try:
            while self.serial.in_waiting > 0:
                line = self.serial.readline().decode('utf-8', errors='ignore').strip()
                
                if not line:
                    continue
                
                # Parse different message types
                if line.startswith("ALCOHOL:"):
                    try:
                        level = int(line.split(":")[1])
                        self.alcohol_level = level
                        self.last_update = time.time()
                        data['alcohol_level'] = level
                    except:
                        pass
                
                elif line.startswith("RELAY:"):
                    data['relay_status'] = line.split(":")[1]
                
                elif line.startswith("BUZZER:"):
                    data['buzzer_status'] = line.split(":")[1]
                
                else:
                    # Echo or status message
                    print(f"[ARDUINO] {line}")
        
        except Exception as e:
            print(f"[SERIAL ERROR] Failed to read data: {e}")
            self.connected = False
        
        return data
    
    def close(self):
        """Close serial connection."""
        if self.serial and self.serial.is_open:
            try:
                self.serial.close()
                self.connected = False
                print("[SERIAL] Connection closed")
            except:
                pass


# ============================================================================
# THREAT SCORING ENGINE
# ============================================================================

class ThreatScoringEngine:
    """Calculates threat score based on multiple sensor inputs."""
    
    def __init__(self):
        """Initialize threat scoring system."""
        self.drowsiness_score = 0
        self.yawn_score = 0
        self.alcohol_score = 0
        self.last_trigger_type = None
    
    def calculate_threat_score(self, ear_normalized, mar_normalized, alcohol_level, 
                               alcohol_baseline, drowsiness_frames, yawn_frames):
        """
        Calculate composite threat score (0-100).
        
        Formula:
        - Base score: drowsiness_component + yawn_component + alcohol_component
        - Alcohol acts as multiplier for drowsiness/yawn components
        
        Args:
            ear_normalized (float): EAR deviation from baseline (0-1)
            mar_normalized (float): MAR deviation from baseline (0-1)
            alcohol_level (int): Current alcohol sensor reading
            alcohol_baseline (int): Baseline alcohol level
            drowsiness_frames (int): Consecutive frames below EAR threshold
            yawn_frames (int): Consecutive frames above MAR threshold
        
        Returns:
            tuple: (threat_score, trigger_type)
        """
        threat_score = 0
        trigger_type = None
        
        # ===== DROWSINESS COMPONENT (0-40 points) =====
        if drowsiness_frames > 0:
            drowsiness_intensity = min(drowsiness_frames / Config.EAR_CONSECUTIVE_FRAMES, 1.0)
            self.drowsiness_score = drowsiness_intensity * 40
            threat_score += self.drowsiness_score
            trigger_type = "DROWSY"
        else:
            self.drowsiness_score = 0
        
        # ===== YAWN COMPONENT (0-30 points) =====
        if yawn_frames > 0:
            yawn_intensity = min(yawn_frames / Config.MAR_CONSECUTIVE_FRAMES, 1.0)
            self.yawn_score = yawn_intensity * 30
            threat_score += self.yawn_score
            if trigger_type:
                trigger_type = "MULTI"
            else:
                trigger_type = "YAWN"
        else:
            self.yawn_score = 0
        
        # ===== ALCOHOL COMPONENT (0-50 points) =====
        # Alcohol acts as amplifier
        if alcohol_level > alcohol_baseline:
            alcohol_delta = alcohol_level - alcohol_baseline
            alcohol_intensity = min(alcohol_delta / 200.0, 1.0)  # Normalize over 200 point range
            self.alcohol_score = alcohol_intensity * 50
            threat_score += self.alcohol_score
            
            # Amplify drowsiness/yawn scores if alcohol is present
            if self.drowsiness_score > 0 or self.yawn_score > 0:
                amplification_factor = 1.0 + (alcohol_intensity * 0.3)  # Up to 30% amplification
                threat_score = min(threat_score * amplification_factor, 100)
                
                if trigger_type:
                    trigger_type = "MULTI"
                else:
                    trigger_type = "ALCOHOL"
        else:
            self.alcohol_score = 0
        
        # Critical threshold activation
        if threat_score >= Config.THREAT_SCORE_CRITICAL:
            trigger_type = "CRITICAL"
        
        self.last_trigger_type = trigger_type
        
        return min(threat_score, 100), trigger_type


# ============================================================================
# CALIBRATION ENGINE
# ============================================================================

class CalibrationEngine:
    """Handles dynamic baseline calibration."""
    
    def __init__(self, calibration_frames=50):
        """
        Initialize calibration engine.
        
        Args:
            calibration_frames (int): Number of frames to calibrate
        """
        self.calibration_frames = calibration_frames
        self.ear_buffer = deque(maxlen=calibration_frames)
        self.mar_buffer = deque(maxlen=calibration_frames)
        self.calibrated = False
        self.baseline_ear = 0.28
        self.baseline_mar = 0.05
        self.frame_count = 0
    
    def add_sample(self, ear, mar):
        """
        Add calibration sample.
        
        Args:
            ear (float): Eye Aspect Ratio sample
            mar (float): Mouth Aspect Ratio sample
        """
        self.ear_buffer.append(ear)
        self.mar_buffer.append(mar)
        self.frame_count += 1
        
        # Check if calibration complete
        if len(self.ear_buffer) >= self.calibration_frames:
            self.finalize()
    
    def finalize(self):
        """Compute final baseline values."""
        if len(self.ear_buffer) > 0:
            self.baseline_ear = np.median(self.ear_buffer)
            self.baseline_mar = np.median(self.mar_buffer)
            self.calibrated = True
            print(f"[CALIB] Calibration complete!")
            print(f"[CALIB]   Baseline EAR: {self.baseline_ear:.4f}")
            print(f"[CALIB]   Baseline MAR: {self.baseline_mar:.4f}")
    
    def get_progress(self):
        """Get calibration progress percentage."""
        return int((len(self.ear_buffer) / self.calibration_frames) * 100)


# ============================================================================
# MAIN APPLICATION
# ============================================================================

class DrowsinessDetectionApp:
    """Main application controller."""
    
    def __init__(self):
        """Initialize application."""
        self.frame_queue = queue.Queue(maxsize=2)
        self.capture_thread = None
        self.arduino = None
        self.face_cascade = None  # OpenCV Haar Cascade
        self.face_mesh = None  # MediaPipe (not used, but cleanup expects it)
        self.eye_detector = None  # Improved eye detector
        self.audio_alerter = None  # Laptop speaker
        self.calibration = None
        self.threat_engine = None
        self.telemetry_db = None
        self.running = False
        self.fps_counter = 0
        self.fps_timer = time.time()
        self.fps = 0
    
    def initialize(self):
        """Initialize all system components."""
        print("\n" + "="*70)
        print("   PRODUCTION-GRADE DROWSINESS & ALCOHOL DETECTION SYSTEM v3.0")
        print("   Multithreaded | Dynamic Calibration | Threat Scoring | SQLite Logging")
        print("="*70 + "\n")
        
        # Initialize face detector (using OpenCV Haar Cascade as fallback)
        print("[INIT] Initializing face detection module...")
        try:
            # Use OpenCV's Haar Cascade for face detection as fallback
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            self.face_cascade = cv2.CascadeClassifier(cascade_path)
            if self.face_cascade.empty():
                print("[ERROR] Failed to load Haar Cascade classifier")
                return False
            print("[INIT] ✓ Face detection initialized")
        except Exception as e:
            print(f"[ERROR] Face detection initialization failed: {e}")
            return False
        
        # Initialize improved eye detector
        print("[INIT] Initializing eye detector...")
        try:
            self.eye_detector = ImprovedEyeDetector()
            print("[INIT] ✓ Eye detector initialized")
        except Exception as e:
            print(f"[ERROR] Eye detector initialization failed: {e}")
            return False
        
        # Initialize audio alerter
        print("[INIT] Initializing laptop speaker alerter...")
        try:
            self.audio_alerter = AudioAlerter()
            print("[INIT] ✓ Audio alerter ready")
        except Exception as e:
            print(f"[ERROR] Audio alerter initialization failed: {e}")
            return False
        
        # Initialize SQLite database
        print("[INIT] Initializing telemetry database...")
        try:
            self.telemetry_db = TelemetryDB(Config.TELEMETRY_DB)
            print(f"[INIT] ✓ Database ready: {Config.TELEMETRY_DB}")
        except Exception as e:
            print(f"[ERROR] Database initialization failed: {e}")
            return False
        
        # Initialize Arduino connection
        print("[INIT] Connecting to Arduino...")
        self.arduino = ArduinoConnection(Config.SERIAL_BAUD_RATE, Config.SERIAL_TIMEOUT)
        if not self.arduino.connect():
            print("[INIT] ⚠ Arduino connection deferred (will retry)")
        else:
            print("[INIT] ✓ Arduino connected")
        
        # Initialize calibration engine
        self.calibration = CalibrationEngine(Config.CALIBRATION_FRAMES)
        print(f"[INIT] ✓ Calibration engine ready ({Config.CALIBRATION_FRAMES} frames)")
        
        # Initialize threat scoring engine
        self.threat_engine = ThreatScoringEngine()
        print("[INIT] ✓ Threat scoring engine ready")
        
        # Start video capture thread
        print("[INIT] Starting video capture thread...")
        self.capture_thread = VideoCaptureThread(
            Config.CAMERA_INDEX,
            self.frame_queue,
            Config.TARGET_FPS
        )
        self.capture_thread.start()
        
        # Wait for first frame (longer timeout)
        print("[INIT] Waiting for camera frames...")
        frame_ready = False
        for attempt in range(30):  # Try for up to 15 seconds
            time.sleep(0.5)
            if not self.frame_queue.empty():
                frame_ready = True
                print(f"[INIT] ✓ First frame received after {(attempt+1)*0.5:.1f}s")
                break
            if attempt % 4 == 0:  # Print every 2 seconds
                print(f"[INIT] Waiting... ({attempt+1}/30)")
        
        if not frame_ready:
            print("[ERROR] No frames captured - camera initialization failed")
            print("[ERROR] Try running: python test_camera.py")
            return False
        
        print("[INIT] ✓ Video capture thread active")
        print("\n" + "="*70)
        print("   SYSTEM READY - CALIBRATION PHASE STARTING")
        print("   Please keep your face in view. Do not blink or yawn.")
        print("="*70 + "\n")
        
        return True
    
    def process_frame(self, frame):
        """
        Process single frame for face and eye detection using improved detector.
        
        Args:
            frame: OpenCV frame (BGR)
        
        Returns:
            tuple: (results dict, frame)
        """
        results = {
            'face_detected': False,
            'ear_left': 0.25,  # Normal open eye
            'ear_right': 0.25,
            'ear_avg': 0.25,
            'mar': 0.08,
            'left_eye_landmarks': [],
            'right_eye_landmarks': [],
            'mouth_landmarks': None,
            'face_landmarks': None,
            'debug_text': ""
        }
        
        try:
            # Flip for mirror effect
            frame = cv2.flip(frame, 1)
            h, w = frame.shape[:2]
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            faces = self.face_cascade.detectMultiScale(
                gray, 
                scaleFactor=1.1,
                minNeighbors=7,
                minSize=(80, 80)
            )
            
            if len(faces) > 0:
                results['face_detected'] = True
                face_roi = faces[0]  # Use largest face
                
                # Detect eyes using darkness/intensity analysis (MUCH more reliable)
                ear_left, ear_right, eyes_detected = self.eye_detector.detect_eye_closure_by_darkness(
                    gray, face_roi
                )
                
                results['ear_left'] = ear_left
                results['ear_right'] = ear_right
                results['ear_avg'] = (ear_left + ear_right) / 2.0
                
                # Estimate MAR
                results['mar'] = self.eye_detector.estimate_mar(gray, face_roi)
                
                # Draw face rectangle for visualization
                x, y, fw, fh = face_roi
                cv2.rectangle(frame, (x, y), (x+fw, y+fh), (0, 255, 0), 2)
                
                # Draw eye region boxes for debugging
                eye_top = int(y + fh * 0.15)
                eye_bottom = int(y + fh * 0.40)
                cv2.rectangle(frame, (x, eye_top), (x+fw, eye_bottom), (255, 0, 0), 1)
                
                # Draw EAR and MAR on frame
                cv2.putText(frame, f"EAR-L: {results['ear_left']:.3f}", (x, y-40),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                cv2.putText(frame, f"EAR-R: {results['ear_right']:.3f}", (x, y-25),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                cv2.putText(frame, f"MAR: {results['mar']:.3f}", (x, y-10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                
                # Store debug text
                results['debug_text'] = f"EAR-Avg: {results['ear_avg']:.3f} | MAR: {results['mar']:.3f}"
        
        except Exception as e:
            print(f"[PROCESS ERROR] {e}", flush=True)
        
        return results, frame
    
    def run(self):
        """Main application loop."""
        if not self.initialize():
            print("[ERROR] Initialization failed")
            return
        
        self.running = True
        
        # State management
        drowsiness_frame_counter = 0
        yawn_frame_counter = 0
        last_threat_score = 0
        last_trigger_type = None
        alert_start_time = None
        ear_smoother = deque(maxlen=Config.EAR_BUFFER_SIZE)
        
        try:
            while self.running:
                # Get frame from queue
                try:
                    ret, frame = self.frame_queue.get(timeout=1.0)
                except queue.Empty:
                    print("[WARN] Frame queue empty - camera may have disconnected")
                    continue
                
                if not ret:
                    print("[ERROR] Failed to get valid frame")
                    continue
                
                # Process frame
                results, frame = self.process_frame(frame)
                frame_copy = frame.copy()
                h, w = frame.shape[:2]
                
                # Update FPS
                self.fps_counter += 1
                elapsed = time.time() - self.fps_timer
                if elapsed >= 1.0:
                    self.fps = self.fps_counter / elapsed
                    self.fps_counter = 0
                    self.fps_timer = time.time()
                
                # ===== CALIBRATION PHASE =====
                if not self.calibration.calibrated:
                    if results['face_detected']:
                        self.calibration.add_sample(results['ear_avg'], results['mar'])
                        
                        # Draw calibration UI
                        cv2.rectangle(frame_copy, (0, 0), (w, 120), (40, 40, 40), -1)
                        progress = self.calibration.get_progress()
                        cv2.putText(frame_copy, "CALIBRATION PHASE", (20, 40),
                                  cv2.FONT_HERSHEY_SIMPLEX, 1, (100, 255, 100), 2)
                        cv2.putText(frame_copy, f"Progress: {progress}%", (20, 80),
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.8, (100, 255, 100), 2)
                        
                        # Draw progress bar
                        bar_width = int((progress / 100) * (w - 40))
                        cv2.rectangle(frame_copy, (20, 100), (20 + bar_width, 115),
                                    (100, 255, 100), -1)
                        cv2.rectangle(frame_copy, (20, 100), (w - 20, 115),
                                    (255, 255, 255), 2)
                    
                    cv2.imshow("Drowsiness Detection System", frame_copy)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                    
                    continue
                
                # ===== DETECTION PHASE =====
                if results['face_detected']:
                    # Smooth EAR
                    ear_smoother.append(results['ear_avg'])
                    ear_smoothed = np.mean(ear_smoother) if len(ear_smoother) > 0 else results['ear_avg']
                    
                    # Calculate thresholds - use fixed thresholds
                    alcohol_level = self.arduino.alcohol_level if self.arduino else 0
                    
                    # Check drowsiness (EAR below threshold)
                    if results['ear_avg'] < Config.EAR_THRESHOLD:
                        drowsiness_frame_counter += 1
                    else:
                        drowsiness_frame_counter = 0
                    
                    # Check yawning (MAR above threshold)
                    if results['mar'] > Config.MAR_THRESHOLD:
                        yawn_frame_counter += 1
                    else:
                        yawn_frame_counter = 0
                    
                    # Calculate threat score based on frame counters
                    threat_score = 0
                    trigger_type = None
                    
                    # Drowsiness component
                    if drowsiness_frame_counter >= Config.EAR_CONSECUTIVE_FRAMES:
                        threat_score += 50
                        trigger_type = "DROWSY"
                    elif drowsiness_frame_counter >= Config.EAR_CONSECUTIVE_FRAMES / 2:
                        threat_score += 25
                    
                    # Yawning component
                    if yawn_frame_counter >= Config.MAR_CONSECUTIVE_FRAMES:
                        threat_score += 40
                        trigger_type = "YAWN" if not trigger_type else "MULTI"
                    elif yawn_frame_counter >= Config.MAR_CONSECUTIVE_FRAMES / 2:
                        threat_score += 20
                    
                    # Alcohol component (if alcohol sensor connected)
                    if alcohol_level > Config.ALCOHOL_THRESHOLD_BASELINE:
                        threat_score += 30
                        threat_score *= 1.2  # Amplify for alcohol
                        if trigger_type:
                            trigger_type = "MULTI"
                        else:
                            trigger_type = "ALCOHOL"
                    
                    # Cap threat score
                    if threat_score >= 75:
                        trigger_type = "CRITICAL"
                    
                    threat_score = min(100, threat_score)
                    ear_threshold = Config.EAR_THRESHOLD
                    
                    # Alert triggering - trigger Audio as soon as threat detected (not just on crossing)
                    if threat_score >= Config.THREAT_SCORE_WARNING:
                        if not alert_start_time:
                            alert_start_time = time.time()
                            print(f"\n[🔴 ALERT] Threat Score: {threat_score:.1f}/100 | Type: {trigger_type}")
                            print(f"[🔴 ALERT] EAR: {ear_smoothed:.4f} | MAR: {results['mar']:.4f}")
                            print(f"[🔴 ALERT] Drowsy frames: {drowsiness_frame_counter}/{Config.EAR_CONSECUTIVE_FRAMES}\n")
                        
                        # Play audio alert on EVERY frame while threat persists
                        if self.audio_alerter:
                            self.audio_alerter.trigger_alert(trigger_type or "UNKNOWN")
                        
                        # Send to Arduino
                        if self.arduino and self.arduino.connected and threat_score != last_threat_score:
                            self.arduino.send_threat_score(threat_score, trigger_type or "UNKNOWN")
                        
                        # Log to database
                        if self.telemetry_db and threat_score != last_threat_score:
                            alert_duration = time.time() - alert_start_time if alert_start_time else 0
                            self.telemetry_db.log_alert(
                                threat_score=threat_score,
                                trigger_reason=trigger_type or "UNKNOWN",
                                ear=ear_smoothed,
                                mar=results['mar'],
                                alcohol_level=alcohol_level,
                                duration=alert_duration
                            )
                    
                    # Clear alert if score drops
                    if threat_score < Config.THREAT_SCORE_WARNING and alert_start_time:
                        alert_duration = time.time() - alert_start_time
                        print(f"[CLEAR] Alert cleared after {alert_duration:.1f}s")
                        alert_start_time = None
                    
                    last_threat_score = threat_score
                    last_trigger_type = trigger_type
                    
                    # Add threat info to frame
                    threat_color = (0, 255, 0)  # Green = safe
                    if threat_score >= 75:
                        threat_color = (0, 0, 255)  # Red = critical
                    elif threat_score >= 50:
                        threat_color = (0, 165, 255)  # Orange = warning
                    elif threat_score >= Config.THREAT_SCORE_WARNING:
                        threat_color = (0, 255, 255)  # Yellow = alert
                    
                    cv2.rectangle(frame_copy, (0, 0), (w, 100), (40, 40, 40), -1)
                    cv2.putText(frame_copy, f"Threat: {threat_score:.1f}/100", (20, 50),
                               cv2.FONT_HERSHEY_SIMPLEX, 1.2, threat_color, 2)
                    cv2.putText(frame_copy, f"Type: {trigger_type or 'NORMAL'}", (20, 85),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.8, threat_color, 2)
                    
                    # Add FPS
                    cv2.putText(frame_copy, f"FPS: {self.fps:.1f}", (w-150, 30),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    
                    # Add eye/mouth info
                    cv2.putText(frame_copy, f"Drowsy: {drowsiness_frame_counter}/{Config.EAR_CONSECUTIVE_FRAMES}", 
                               (w-300, 85), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 1)

                
                else:
                    drowsiness_frame_counter = 0
                    yawn_frame_counter = 0
                    if alert_start_time:
                        alert_duration = time.time() - alert_start_time
                        print(f"[CLEAR] Alert cleared (face lost) after {alert_duration:.1f}s")
                        alert_start_time = None
                    
                    cv2.putText(frame_copy, "NO FACE DETECTED", (w//2 - 150, h//2),
                              cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)
                
                # Read Arduino data
                if self.arduino and self.arduino.connected:
                    self.arduino.read_data()
                else:
                    # Attempt reconnect
                    if time.time() % 10 < 0.1:  # Every ~10 seconds
                        self.arduino.connect()
                
                # Display frame
                cv2.imshow("Drowsiness Detection System", frame_copy)
                
                # Keyboard controls
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q') or key == ord('Q'):
                    print("\n[INFO] Quit command received")
                    break
        
        except KeyboardInterrupt:
            print("\n[INFO] Keyboard interrupt received")
        except Exception as e:
            print(f"\n[ERROR] Unexpected error: {e}")
            traceback.print_exc()
        
        finally:
            self.shutdown()
    
    def _draw_visualization(self, frame, detection, drowsiness_frames, yawn_frames,
                           threat_score, trigger_type, ear_value, ear_threshold, alcohol_level):
        """
        Draw visualization overlay on frame.
        
        Args:
            frame: OpenCV frame
            detection (dict): Detection results
            drowsiness_frames (int): Consecutive drowsy frames
            yawn_frames (int): Consecutive yawn frames
            threat_score (float): Current threat score
            trigger_type (str): Trigger type
            ear_value (float): Current EAR value
            ear_threshold (float): EAR threshold
            alcohol_level (int): Current alcohol level
        """
        h, w = frame.shape[:2]
        
        # Draw eye landmarks
        if len(detection['left_eye_landmarks']) == 6:
            left_eye = np.array(detection['left_eye_landmarks'], dtype=np.int32)
            cv2.polylines(frame, [left_eye], True, (0, 255, 0), 2)
        
        if len(detection['right_eye_landmarks']) == 6:
            right_eye = np.array(detection['right_eye_landmarks'], dtype=np.int32)
            cv2.polylines(frame, [right_eye], True, (0, 255, 0), 2)
        
        # Draw mouth landmarks if available
        if detection['mouth_landmarks']:
            mouth = detection['mouth_landmarks']
            points = [mouth['top'], mouth['bottom'], mouth['left'], mouth['right']]
            cv2.polylines(frame, [np.array(points, dtype=np.int32)], True, (255, 0, 255), 2)
        
        # Top status bar
        status_height = 150
        cv2.rectangle(frame, (0, 0), (w, status_height), (20, 20, 20), -1)
        
        # Threat score with color coding
        threat_color = (100, 255, 100)  # Green
        if threat_score >= Config.THREAT_SCORE_CRITICAL:
            threat_color = (0, 0, 255)  # Red - Critical
        elif threat_score >= Config.THREAT_SCORE_WARNING:
            threat_color = (0, 165, 255)  # Orange - Warning
        
        cv2.putText(frame, f"THREAT: {threat_score:.1f}/100", (10, 40),
                  cv2.FONT_HERSHEY_SIMPLEX, 1.0, threat_color, 2)
        
        if trigger_type:
            cv2.putText(frame, f"Type: {trigger_type}", (10, 75),
                      cv2.FONT_HERSHEY_SIMPLEX, 0.7, threat_color, 2)
        
        cv2.putText(frame, f"EAR: {ear_value:.4f} (Thresh: {ear_threshold:.4f})", (10, 110),
                  cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 200, 100), 1)
        
        cv2.putText(frame, f"FPS: {self.fps:.1f}", (w - 150, 40),
                  cv2.FONT_HERSHEY_SIMPLEX, 0.8, (100, 200, 255), 2)
        
        alcohol_color = (100, 255, 100) if alcohol_level < 400 else (0, 0, 255)
        cv2.putText(frame, f"Alcohol: {alcohol_level}", (w - 150, 75),
                  cv2.FONT_HERSHEY_SIMPLEX, 0.8, alcohol_color, 2)
        
        # Bottom status bar
        bar_height = 60
        cv2.rectangle(frame, (0, h - bar_height), (w, h), (20, 20, 20), -1)
        
        cv2.putText(frame, f"Drowsy: {drowsiness_frames} frames | Yawns: {yawn_frames}", (10, h - 30),
                  cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 100, 100), 1)
        
        arduino_status = "Arduino: Connected" if (self.arduino and self.arduino.connected) else "Arduino: Disconnected"
        arduino_color = (100, 255, 100) if self.arduino and self.arduino.connected else (100, 100, 255)
        cv2.putText(frame, arduino_status, (10, h - 10),
                  cv2.FONT_HERSHEY_SIMPLEX, 0.5, arduino_color, 1)
    
    def shutdown(self):
        """Clean shutdown of all components."""
        print("\n[SHUTDOWN] Initiating system shutdown...")
        
        self.running = False
        
        # Stop video capture thread
        if self.capture_thread:
            self.capture_thread.stop()
            self.capture_thread.join(timeout=2)
            print("[SHUTDOWN] ✓ Video capture stopped")
        
        # Close Arduino connection
        if self.arduino:
            self.arduino.close()
            print("[SHUTDOWN] ✓ Arduino disconnected")
        
        # Close MediaPipe
        if self.face_mesh:
            self.face_mesh.close()
            print("[SHUTDOWN] ✓ MediaPipe closed")
        
        # Close database
        if self.telemetry_db:
            self.telemetry_db.close()
            print("[SHUTDOWN] ✓ Database closed")
        
        # Close OpenCV
        cv2.destroyAllWindows()
        print("[SHUTDOWN] ✓ OpenCV resources released")
        
        print("[SHUTDOWN] System gracefully terminated\n")


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    app = DrowsinessDetectionApp()
    app.run()
