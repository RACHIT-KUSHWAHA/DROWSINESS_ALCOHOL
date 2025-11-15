"""
Alcohol and Drowsiness Detection System - Eye Monitoring Module
================================================================
Uses Google MediaPipe Face Mesh for real-time eye aspect ratio (EAR) calculation
to detect drowsiness through webcam-based eye closure monitoring.

Features:
- Real-time face and eye landmark detection (478 facial landmarks)
- Eye Aspect Ratio (EAR) calculation for drowsiness detection
- Serial communication with Arduino for alert system control
- Automatic Arduino port detection
- Live video feed with visual overlays and statistics

Author: Alcohol & Drowsiness Detection System
Version: 2.0
"""

import warnings
warnings.filterwarnings('ignore', category=UserWarning)

import cv2
import serial
import serial.tools.list_ports
import time
import numpy as np
import mediapipe as mp
import sys

# Configuration Parameters
EYE_AR_THRESH = 0.20        # Eye Aspect Ratio threshold for closure detection
EYE_AR_CONSEC_FRAMES = 48   # Number of consecutive frames below threshold (~2 seconds at 24 fps)
SERIAL_BAUD_RATE = 9600     # Serial communication baud rate
CAMERA_INDEX = 0            # Default camera index (0 = primary webcam)

# System State Variables
COUNTER = 0                 # Frame counter for eye closure duration
ALARM_ON = False            # Alert state flag
TOTAL_BLINKS = 0            # Total blink count during session
CURRENT_ALCOHOL_LEVEL = 0   # Current alcohol level from Arduino

# MediaPipe Face Mesh Initialization
mp_face_mesh = mp.solutions.face_mesh
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

# Eye Landmark Indices (MediaPipe Face Mesh - 468 landmarks)
LEFT_EYE = [362, 385, 387, 263, 373, 380]
RIGHT_EYE = [33, 160, 158, 133, 153, 144]

def find_arduino_port():
    """
    Automatically detect Arduino COM port by scanning available serial ports.
    
    Returns:
        str: COM port identifier (e.g., 'COM3') or None if not found
    """
    ports = serial.tools.list_ports.comports()
    arduino_ports = []
    
    for port in ports:
        if any(keyword in port.description.upper() for keyword in ['ARDUINO', 'CH340', 'USB-SERIAL', 'USB SERIAL', 'CP210']):
            arduino_ports.append(port.device)
    
    return arduino_ports[0] if arduino_ports else None

def euclidean_distance(point1, point2):
    """
    Calculate Euclidean distance between two 2D points.
    
    Args:
        point1 (tuple): First point coordinates (x, y)
        point2 (tuple): Second point coordinates (x, y)
    
    Returns:
        float: Euclidean distance between the points
    """
    return np.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)

def eye_aspect_ratio(eye_landmarks):
    """
    Calculate Eye Aspect Ratio (EAR) from MediaPipe facial landmarks.
    EAR indicates eye openness and is used for drowsiness detection.
    
    Formula: EAR = (||p2-p6|| + ||p3-p5||) / (2 * ||p1-p4||)
    
    Args:
        eye_landmarks (list): List of 6 eye landmark coordinates [(x,y), ...]
    
    Returns:
        float: Eye Aspect Ratio (typically 0.2-0.3 for open eyes, <0.2 for closed)
    """
    A = euclidean_distance(eye_landmarks[1], eye_landmarks[5])
    B = euclidean_distance(eye_landmarks[2], eye_landmarks[4])
    C = euclidean_distance(eye_landmarks[0], eye_landmarks[3])
    
    if C < 0.01:
        return 0.3
    
    ear = (A + B) / (2.0 * C)
    return ear

def get_eye_landmarks(face_landmarks, eye_indices, frame_width, frame_height):
    """
    Extract eye landmark pixel coordinates from MediaPipe face mesh.
    
    Args:
        face_landmarks: MediaPipe face mesh landmarks object
        eye_indices (list): List of landmark indices for the eye
        frame_width (int): Video frame width in pixels
        frame_height (int): Video frame height in pixels
    
    Returns:
        list: List of (x, y) pixel coordinates for eye landmarks
    """
    landmarks = []
    for idx in eye_indices:
        landmark = face_landmarks.landmark[idx]
        x = int(landmark.x * frame_width)
        y = int(landmark.y * frame_height)
        landmarks.append((x, y))
    return landmarks

def main():
    """
    Main application loop for drowsiness detection system.
    Initializes camera, MediaPipe, Arduino connection, and runs detection loop.
    """
    global COUNTER, ALARM_ON, TOTAL_BLINKS, CURRENT_ALCOHOL_LEVEL
    
    print("\n" + "="*60)
    print("   ALCOHOL & DROWSINESS DETECTION SYSTEM")
    print("   Eye Monitoring Module - Powered by MediaPipe")
    print("="*60 + "\n")
    
    # Initialize MediaPipe Face Mesh
    print("[INFO] Initializing MediaPipe Face Mesh...")
    try:
        face_mesh = mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        print("[SUCCESS] MediaPipe initialized successfully")
    except Exception as e:
        print(f"[ERROR] MediaPipe initialization failed: {e}")
        input("\nPress Enter to exit...")
        return
    
    # Connect to Arduino
    print("\n[INFO] Searching for Arduino...")
    arduino_port = find_arduino_port()
    arduino = None
    
    if arduino_port is None:
        print("[WARNING] Arduino not detected automatically")
        response = input("Enter COM port manually (or press Enter to skip): ").strip()
        if response:
            arduino_port = response
        else:
            print("[INFO] Running in test mode without Arduino")
            arduino = None
    else:
        print(f"[SUCCESS] Arduino detected on {arduino_port}")
    
    if arduino_port:
        try:
            arduino = serial.Serial(arduino_port, SERIAL_BAUD_RATE, timeout=1)
            time.sleep(2)
            print("[SUCCESS] Serial connection established")
            
            # Wait for Arduino READY signal
            timeout = time.time() + 35
            print("[INFO] Waiting for Arduino initialization...")
            while time.time() < timeout:
                if arduino.in_waiting > 0:
                    response = arduino.readline().decode('utf-8', errors='ignore').strip()
                    if response:
                        print(f"[ARDUINO] {response}")
                    if "SYSTEM_READY" in response:
                        break
                time.sleep(0.1)
        except Exception as e:
            print(f"[ERROR] Arduino connection failed: {e}")
            print("[INFO] Continuing in test mode")
            arduino = None
    
    # Initialize video capture
    print("\n[INFO] Initializing camera...")
    cap = cv2.VideoCapture(CAMERA_INDEX)
    
    if not cap.isOpened():
        print(f"[ERROR] Camera at index {CAMERA_INDEX} could not be opened")
        print("[TIP] Try changing CAMERA_INDEX to 1 or 2")
        if arduino:
            arduino.close()
        face_mesh.close()
        input("\nPress Enter to exit...")
        return
    
    # Configure camera properties
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)
    
    print("[SUCCESS] Camera initialized successfully")
    print("\n" + "="*60)
    print("   SYSTEM ACTIVE - Monitoring Started")
    print("="*60)
    print("\nKEYBOARD CONTROLS:")
    print("  Q - Quit application")
    print("  R - Reset blink counter")
    print("  S - Save screenshot")
    print("\nSYSTEM PARAMETERS:")
    print(f"  EAR Threshold: {EYE_AR_THRESH}")
    print(f"  Alert Duration: {EYE_AR_CONSEC_FRAMES} frames (~2 seconds)")
    print(f"  Alcohol Limit: 400")
    print("\n" + "="*60 + "\n")
    
    try:
        frame_count = 0
        fps_start_time = time.time()
        fps = 0
        last_blink_state = False
        
        while True:
            ret, frame = cap.read()
            if not ret:
                print("[ERROR] Failed to capture frame from camera")
                break
            
            frame_count += 1
            
            # Calculate frames per second
            if frame_count % 30 == 0:
                fps_end_time = time.time()
                fps = 30 / (fps_end_time - fps_start_time)
                fps_start_time = fps_end_time
            
            # Flip frame for mirror effect
            frame = cv2.flip(frame, 1)
            frame_height, frame_width = frame.shape[:2]
            
            # Convert BGR to RGB for MediaPipe processing
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Process frame with MediaPipe Face Mesh
            results = face_mesh.process(rgb_frame)
            
            face_detected = False
            ear = 0
            
            if results.multi_face_landmarks:
                face_detected = True
                for face_landmarks in results.multi_face_landmarks:
                    # Extract eye landmark coordinates
                    left_eye_landmarks = get_eye_landmarks(face_landmarks, LEFT_EYE, frame_width, frame_height)
                    right_eye_landmarks = get_eye_landmarks(face_landmarks, RIGHT_EYE, frame_width, frame_height)
                    
                    # Calculate EAR for both eyes
                    leftEAR = eye_aspect_ratio(left_eye_landmarks)
                    rightEAR = eye_aspect_ratio(right_eye_landmarks)
                    
                    # Average EAR
                    ear = (leftEAR + rightEAR) / 2.0
                    
                    # Draw eye contours
                    left_eye_points = np.array(left_eye_landmarks, dtype=np.int32)
                    right_eye_points = np.array(right_eye_landmarks, dtype=np.int32)
                    cv2.polylines(frame, [left_eye_points], True, (0, 255, 0), 2)
                    cv2.polylines(frame, [right_eye_points], True, (0, 255, 0), 2)
                    
                    # Check if EAR is below threshold
                    if ear < EYE_AR_THRESH:
                        COUNTER += 1
                        
                        # Check if threshold duration exceeded
                        if COUNTER >= EYE_AR_CONSEC_FRAMES:
                            if not ALARM_ON:
                                ALARM_ON = True
                                if arduino:
                                    try:
                                        arduino.write(b'E')
                                    except:
                                        pass
                                print(f"[ALERT] Drowsiness detected - EAR: {ear:.3f}")
                            
                            # Display warning banner
                            cv2.rectangle(frame, (0, 0), (frame_width, 80), (0, 0, 139), -1)
                            cv2.putText(frame, "DROWSINESS ALERT", (int(frame_width/2 - 180), 35),
                                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 3)
                            cv2.putText(frame, "Wake Up!", (int(frame_width/2 - 80), 65),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (100, 200, 255), 2)
                    else:
                        # Count blinks
                        if COUNTER > 5 and COUNTER < EYE_AR_CONSEC_FRAMES and not last_blink_state:
                            TOTAL_BLINKS += 1
                            last_blink_state = True
                        
                        COUNTER = 0
                        last_blink_state = False
                        
                        if ALARM_ON:
                            ALARM_ON = False
                            if arduino:
                                try:
                                    arduino.write(b'N')
                                except:
                                    pass
                            print("[INFO] Eyes open - Normal state")
                    
                    # Display statistics overlay
                    ear_color = (0, 255, 0) if ear >= EYE_AR_THRESH else (0, 165, 255)
                    cv2.putText(frame, f"EAR: {ear:.3f}", (frame_width - 160, 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, ear_color, 2)
                    cv2.putText(frame, f"Closed: {COUNTER}", (frame_width - 160, 60),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, ear_color, 2)
                    cv2.putText(frame, f"Blinks: {TOTAL_BLINKS}", (frame_width - 160, 90),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 200, 255), 2)
            
            # Handle no face detection
            if not face_detected:
                cv2.putText(frame, "No Face Detected", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                COUNTER = 0
                if ALARM_ON:
                    ALARM_ON = False
                    if arduino:
                        try:
                            arduino.write(b'N')
                        except:
                            pass
            
            # Display system information
            cv2.putText(frame, f"FPS: {fps:.1f}", (10, frame_height - 120),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            
            status_text = "Arduino: Connected" if arduino else "Arduino: Disconnected"
            status_color = (100, 255, 100) if arduino else (100, 100, 255)
            cv2.putText(frame, status_text, (10, frame_height - 90),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, status_color, 2)
            
            # Display alcohol level
            alcohol_color = (100, 255, 100) if CURRENT_ALCOHOL_LEVEL < 400 else (0, 0, 255)
            alcohol_text = f"Alcohol: {CURRENT_ALCOHOL_LEVEL}"
            if CURRENT_ALCOHOL_LEVEL >= 400:
                alcohol_text += " - ALERT"
            cv2.putText(frame, alcohol_text, (10, frame_height - 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, alcohol_color, 2)
            
            cv2.putText(frame, "Threshold: 400", (10, frame_height - 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 2)
            
            # Read Arduino serial data
            if arduino:
                try:
                    if arduino.in_waiting > 0:
                        response = arduino.readline().decode('utf-8', errors='ignore').strip()
                        if response:
                            print(f"[ARDUINO] {response}")
                            
                            # Parse alcohol level
                            if "Level" in response and "=" in response:
                                try:
                                    level_str = response.split("=")[-1].strip()
                                    CURRENT_ALCOHOL_LEVEL = int(level_str)
                                except:
                                    pass
                except:
                    pass
            
            # Display video frame
            cv2.imshow("Alcohol & Drowsiness Detection System", frame)
            
            # Handle keyboard input
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == ord('Q'):
                print("\n[INFO] Shutting down system...")
                break
            elif key == ord('r') or key == ord('R'):
                TOTAL_BLINKS = 0
                print("[INFO] Blink counter reset")
            elif key == ord('s') or key == ord('S'):
                filename = f"screenshot_{int(time.time())}.jpg"
                cv2.imwrite(filename, frame)
                print(f"[INFO] Screenshot saved: {filename}")
    
    except KeyboardInterrupt:
        print("\n[INFO] Keyboard interrupt detected - Exiting...")
    except Exception as e:
        print(f"\n[ERROR] Unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # System cleanup
        print("\n[INFO] Cleaning up resources...")
        if arduino:
            try:
                arduino.write(b'N')
                time.sleep(0.1)
                arduino.close()
                print("[INFO] Arduino disconnected")
            except:
                pass
        
        try:
            face_mesh.close()
            print("[INFO] MediaPipe resources released")
        except:
            pass
        
        try:
            cap.release()
            cv2.destroyAllWindows()
            print("[INFO] Camera released")
        except:
            pass
        
        print(f"\n{'='*60}")
        print("SESSION SUMMARY")
        print(f"{'='*60}")
        print(f"Total Blinks: {TOTAL_BLINKS}")
        print(f"Total Frames Processed: {frame_count}")
        print(f"{'='*60}")
        print("Thank you for using the Drowsiness Detection System")
        print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
