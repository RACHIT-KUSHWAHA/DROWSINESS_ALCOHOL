"""
🚨 Eye Detection and Drowsiness Monitoring System 🚨
Uses laptop camera with MediaPipe to detect eye closure and communicates with Arduino
Author: Alcohol & Drowsiness Detection System
Version: 2.0 GenZ Edition 💯✨
"""

import warnings
warnings.filterwarnings('ignore', category=UserWarning)  # Suppress protobuf warnings

import cv2
import serial
import serial.tools.list_ports
import time
import numpy as np
import mediapipe as mp
import sys

# Configuration
EYE_AR_THRESH = 0.20        # Eye Aspect Ratio threshold (MediaPipe optimized)
EYE_AR_CONSEC_FRAMES = 48   # ~2 seconds at 24 fps (adjust based on your camera)
SERIAL_BAUD_RATE = 9600
CAMERA_INDEX = 0            # Change to 1 or 2 if default camera doesn't work

# Initialize counters
COUNTER = 0
ALARM_ON = False
TOTAL_BLINKS = 0
CURRENT_ALCOHOL_LEVEL = 0  # Store current alcohol level from Arduino

# MediaPipe Face Mesh
mp_face_mesh = mp.solutions.face_mesh
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

# Eye landmark indices for MediaPipe Face Mesh (468 landmarks)
# Left eye indices
LEFT_EYE = [362, 385, 387, 263, 373, 380]
# Right eye indices  
RIGHT_EYE = [33, 160, 158, 133, 153, 144]

def find_arduino_port():
    """Automatically detect Arduino COM port"""
    ports = serial.tools.list_ports.comports()
    arduino_ports = []
    
    for port in ports:
        # Look for Arduino in port description
        if any(keyword in port.description.upper() for keyword in ['ARDUINO', 'CH340', 'USB-SERIAL', 'USB SERIAL', 'CP210']):
            arduino_ports.append(port.device)
    
    return arduino_ports[0] if arduino_ports else None

def euclidean_distance(point1, point2):
    """Calculate Euclidean distance between two points"""
    return np.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)

def eye_aspect_ratio(eye_landmarks):
    """
    Calculate Eye Aspect Ratio (EAR) from MediaPipe landmarks
    EAR = (||p2-p6|| + ||p3-p5||) / (2 * ||p1-p4||)
    """
    # Vertical eye landmarks
    A = euclidean_distance(eye_landmarks[1], eye_landmarks[5])
    B = euclidean_distance(eye_landmarks[2], eye_landmarks[4])
    
    # Horizontal eye landmarks
    C = euclidean_distance(eye_landmarks[0], eye_landmarks[3])
    
    # Prevent division by zero
    if C < 0.01:
        return 0.3
    
    # Calculate EAR
    ear = (A + B) / (2.0 * C)
    return ear

def get_eye_landmarks(face_landmarks, eye_indices, frame_width, frame_height):
    """Extract eye landmark coordinates from MediaPipe face mesh"""
    landmarks = []
    for idx in eye_indices:
        landmark = face_landmarks.landmark[idx]
        x = int(landmark.x * frame_width)
        y = int(landmark.y * frame_height)
        landmarks.append((x, y))
    return landmarks

def main():
    global COUNTER, ALARM_ON, TOTAL_BLINKS, CURRENT_ALCOHOL_LEVEL
    
    print("\n" + "🔥"*30)
    print("   ╔═══════════════════════════════════════╗")
    print("   ║  🚨 DROWSINESS DETECTOR 2.0 🚨       ║")
    print("   ║  👁️  Powered by AI × MediaPipe  ⚡   ║")
    print("   ║  🎯 Stay Safe, Stay Woke! 💯         ║")
    print("   ╚═══════════════════════════════════════╝")
    print("🔥"*30 + "\n")
    
    # Initialize MediaPipe Face Mesh
    print("⚡ [LOADING] Initializing AI Brain... 🧠")
    try:
        face_mesh = mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        print("✅ [SUCCESS] AI Brain Online! 🤖💚")
    except Exception as e:
        print(f"❌ [ERROR] AI Brain Failed: {e} 💀")
        input("\nPress Enter to yeet outta here...")
        return
    
    # Connect to Arduino
    print("\n🔌 [SEARCHING] Looking for Arduino homie... 🤖")
    arduino_port = find_arduino_port()
    arduino = None
    
    if arduino_port is None:
        print("⚠️ [WARNING] Arduino ghosted us fr fr 👻")
        response = input("Enter COM port manually (or just hit Enter to skip): ").strip()
        if response:
            arduino_port = response
        else:
            print("🤷 [INFO] Running solo mode (no Arduino) - Test vibes only ✨")
            arduino = None
    else:
        print(f"✅ [FOUND] Arduino connected on {arduino_port}! Let's gooo! 🎮")
    
    if arduino_port:
        try:
            arduino = serial.Serial(arduino_port, SERIAL_BAUD_RATE, timeout=1)
            time.sleep(2)
            print("🔗 [SUCCESS] Arduino link established! We're in sync! 🤝")
            
            # Wait for READY signal with timeout
            timeout = time.time() + 35
            print("⏳ [WAIT] Arduino warming up... Give it a sec... ☕")
            while time.time() < timeout:
                if arduino.in_waiting > 0:
                    response = arduino.readline().decode('utf-8', errors='ignore').strip()
                    if response:
                        print(f"🤖 [ARDUINO] {response}")
                    if "SYSTEM_READY" in response:
                        break
                time.sleep(0.1)
        except Exception as e:
            print(f"❌ [ERROR] Arduino connection failed: {e} 😭")
            print("🤷 [INFO] Whatever, running test mode anyway 🎭")
            arduino = None
    
    # Start video capture
    print("\n📹 [LOADING] Starting camera... Say cheese! 📸")
    cap = cv2.VideoCapture(CAMERA_INDEX)
    
    if not cap.isOpened():
        print(f"❌ [ERROR] Camera at index {CAMERA_INDEX} ain't working! 💀")
        print("💡 [TIP] Try changing CAMERA_INDEX (maybe try 1 or 2?)")
        if arduino:
            arduino.close()
        face_mesh.close()
        input("\nPress Enter to bounce...")
        return
    
    # Set camera properties
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)
    
    print("✅ [SUCCESS] Camera is lit! 🎥✨")
    print("\n" + "🎮"*30)
    print("   ╔═══════════════════════════════════════╗")
    print("   ║      🚀 SYSTEM ACTIVATED 🚀           ║")
    print("   ║   We're watching you bestie 👀        ║")
    print("   ╚═══════════════════════════════════════╝")
    print("🎮"*30)
    print("\n⌨️  CONTROLS:")
    print("   • Press 'Q' to rage quit 🚪")
    print("   • Press 'R' to reset blink counter 🔄")
    print("   • Press 'S' for screenshot (flex material 📸)")
    print("\n📊 THRESHOLDS:")
    print(f"   • EAR Alert: < {EYE_AR_THRESH} (eye closure detection)")
    print(f"   • Danger Zone: {EYE_AR_CONSEC_FRAMES} frames (~2 sec)")
    print("   • Alcohol Limit: 400 (stay sober, stay safe! 🚫🍺)")
    print("\n" + "🎯"*30 + "\n")
    
    try:
        frame_count = 0
        fps_start_time = time.time()
        fps = 0
        last_blink_state = False
        
        while True:
            ret, frame = cap.read()
            if not ret:
                print("❌ [ERROR] Failed to grab frame - Camera issue? 📹")
                break
            
            frame_count += 1
            
            # Calculate FPS
            if frame_count % 30 == 0:
                fps_end_time = time.time()
                fps = 30 / (fps_end_time - fps_start_time)
                fps_start_time = fps_end_time
            
            # Flip frame horizontally for mirror view
            frame = cv2.flip(frame, 1)
            frame_height, frame_width = frame.shape[:2]
            
            # Convert BGR to RGB for MediaPipe
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Process frame with MediaPipe
            results = face_mesh.process(rgb_frame)
            
            face_detected = False
            ear = 0
            
            if results.multi_face_landmarks:
                face_detected = True
                for face_landmarks in results.multi_face_landmarks:
                    # Get eye landmarks
                    left_eye_landmarks = get_eye_landmarks(face_landmarks, LEFT_EYE, frame_width, frame_height)
                    right_eye_landmarks = get_eye_landmarks(face_landmarks, RIGHT_EYE, frame_width, frame_height)
                    
                    # Calculate EAR for both eyes
                    leftEAR = eye_aspect_ratio(left_eye_landmarks)
                    rightEAR = eye_aspect_ratio(right_eye_landmarks)
                    
                    # Average EAR for both eyes
                    ear = (leftEAR + rightEAR) / 2.0
                    
                    # Draw eye contours in RED
                    left_eye_points = np.array(left_eye_landmarks, dtype=np.int32)
                    right_eye_points = np.array(right_eye_landmarks, dtype=np.int32)
                    cv2.polylines(frame, [left_eye_points], True, (0, 0, 255), 2)  # RED color, thicker line
                    cv2.polylines(frame, [right_eye_points], True, (0, 0, 255), 2)  # RED color, thicker line
                    
                    # LASER BEAM EFFECT - When eyes are closing (EAR below threshold)
                    if ear < EYE_AR_THRESH:
                        # Get center of each eye for laser origin
                        left_eye_center = tuple(np.mean(left_eye_points, axis=0).astype(int))
                        right_eye_center = tuple(np.mean(right_eye_points, axis=0).astype(int))
                        
                        # Calculate laser end points (shoot forward from eyes)
                        laser_length = 200
                        left_laser_end = (left_eye_center[0] + laser_length, left_eye_center[1])
                        right_laser_end = (right_eye_center[0] + laser_length, right_eye_center[1])
                        
                        # Draw GLOWING LASER BEAMS with multiple layers for glow effect
                        # Outer glow (thick, semi-transparent)
                        overlay = frame.copy()
                        cv2.line(overlay, left_eye_center, left_laser_end, (0, 0, 255), 15)
                        cv2.line(overlay, right_eye_center, right_laser_end, (0, 0, 255), 15)
                        cv2.addWeighted(overlay, 0.3, frame, 0.7, 0, frame)
                        
                        # Middle glow
                        cv2.line(frame, left_eye_center, left_laser_end, (0, 50, 255), 8)
                        cv2.line(frame, right_eye_center, right_laser_end, (0, 50, 255), 8)
                        
                        # Inner bright core
                        cv2.line(frame, left_eye_center, left_laser_end, (100, 150, 255), 4)
                        cv2.line(frame, right_eye_center, right_laser_end, (100, 150, 255), 4)
                        
                        # Brightest center line (white/yellow core)
                        cv2.line(frame, left_eye_center, left_laser_end, (200, 255, 255), 2)
                        cv2.line(frame, right_eye_center, right_laser_end, (200, 255, 255), 2)
                        
                        # Add laser impact points (circles at the end)
                        cv2.circle(frame, left_laser_end, 10, (0, 0, 255), -1)
                        cv2.circle(frame, left_laser_end, 5, (200, 255, 255), -1)
                        cv2.circle(frame, right_laser_end, 10, (0, 0, 255), -1)
                        cv2.circle(frame, right_laser_end, 5, (200, 255, 255), -1)
                    
                    # Check if EAR is below threshold
                    if ear < EYE_AR_THRESH:
                        COUNTER += 1
                        
                        # If eyes closed for sufficient frames
                        if COUNTER >= EYE_AR_CONSEC_FRAMES:
                            if not ALARM_ON:
                                ALARM_ON = True
                                if arduino:
                                    try:
                                        arduino.write(b'E')
                                    except:
                                        pass
                                print(f"🚨 [ALERT] DROWSINESS DETECTED! Wake up bestie! EAR: {ear:.3f} 😴💤")
                            
                            # Draw warning banner - AESTHETIC AF
                            cv2.rectangle(frame, (0, 0), (frame_width, 80), (0, 0, 139), -1)
                            cv2.putText(frame, "!!! WAKE UP BESTIE !!!", (int(frame_width/2 - 200), 30),
                                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 3)
                            cv2.putText(frame, "You're Dozing Off! 😴💤", (int(frame_width/2 - 150), 65),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (100, 200, 255), 2)
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
                            print(f"✅ [INFO] Eyes open - You're good fam! 👀✨")
                    
                    # Display stats with AESTHETIC design
                    ear_color = (0, 255, 0) if ear >= EYE_AR_THRESH else (0, 165, 255)
                    cv2.putText(frame, f"👁️ EAR: {ear:.3f}", (frame_width - 180, 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, ear_color, 2)
                    cv2.putText(frame, f"😴 Closed: {COUNTER}", (frame_width - 180, 60),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, ear_color, 2)
                    cv2.putText(frame, f"✨ Blinks: {TOTAL_BLINKS}", (frame_width - 180, 90),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 200, 255), 2)
            
            # If no face detected
            if not face_detected:
                cv2.putText(frame, "👻 No Face Detected - Where u at? 👻", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (147, 20, 255), 2)
                COUNTER = 0
                if ALARM_ON:
                    ALARM_ON = False
                    if arduino:
                        try:
                            arduino.write(b'N')
                        except:
                            pass
            
            # Display system info with AESTHETIC vibes
            cv2.putText(frame, f"⚡ FPS: {fps:.1f}", (10, frame_height - 120),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            
            status_text = "🤖 Arduino: Online ✅" if arduino else "🤖 Arduino: Offline ❌"
            status_color = (100, 255, 100) if arduino else (100, 100, 255)
            cv2.putText(frame, status_text, (10, frame_height - 90),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, status_color, 2)
            
            # Display alcohol level - AESTHETIC color coding
            alcohol_color = (100, 255, 100) if CURRENT_ALCOHOL_LEVEL < 400 else (0, 0, 255)
            alcohol_text = f"🍺 Alcohol: {CURRENT_ALCOHOL_LEVEL}"
            if CURRENT_ALCOHOL_LEVEL >= 400:
                alcohol_text += " - YEET! 🚨"
            cv2.putText(frame, alcohol_text, (10, frame_height - 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, alcohol_color, 2)
            
            # Threshold reference with emoji
            cv2.putText(frame, "📊 Limit: 400", (10, frame_height - 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 2)
            
            # Read Arduino responses
            if arduino:
                try:
                    if arduino.in_waiting > 0:
                        response = arduino.readline().decode('utf-8', errors='ignore').strip()
                        if response:
                            # Print ALL Arduino messages to console with AESTHETIC emojis
                            print(f"🤖 [ARDUINO] {response}")
                            
                            # Parse alcohol level
                            if "Level" in response and "=" in response:
                                try:
                                    level_str = response.split("=")[-1].strip()
                                    CURRENT_ALCOHOL_LEVEL = int(level_str)
                                except:
                                    pass
                            
                            # Check for specific messages - GENZ VIBES
                            if "ALERT" in response:
                                print(f"  🚨 OH NO! {response}")
                            elif "ALCOHOL" in response:
                                print(f"  🍺 BRUH! {response}")
                            elif "DROWSY" in response:
                                print(f"  😴 NAP TIME VIBES! {response}")
                except:
                    pass
            
            # Display frame with AESTHETIC window title
            cv2.imshow("👁️ Drowsiness Detector 2.0 | Stay Woke Bestie! 💯", frame)
            
            # Check for key presses
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == ord('Q'):
                print("\n✌️ [INFO] Peace out! Thanks for using! 🚀")
                break
            elif key == ord('r') or key == ord('R'):
                TOTAL_BLINKS = 0
                print("🔄 [INFO] Blink counter reset! Fresh start! ✨")
            elif key == ord('s') or key == ord('S'):
                filename = f"screenshot_{int(time.time())}.jpg"
                cv2.imwrite(filename, frame)
                print(f"📸 [INFO] Screenshot saved: {filename} - Post it! 🔥")
    
    except KeyboardInterrupt:
        print("\n⚡ [INFO] Ctrl+C detected - Exiting gracefully! 🎭")
    except Exception as e:
        print(f"\n💀 [ERROR] Something went wrong bestie: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        print("\n🛑 [INFO] Shutting down the vibes...")
        if arduino:
            try:
                arduino.write(b'N')
                time.sleep(0.1)
                arduino.close()
                print("🔌 [INFO] Arduino disconnected! Bye robot homie! 🤖👋")
            except:
                pass
        
        try:
            face_mesh.close()
            print("🧠 [INFO] AI Brain powered off! 💤")
        except:
            pass
        
        try:
            cap.release()
            cv2.destroyAllWindows()
            print("📹 [INFO] Camera stopped! No more pics! 📸")
        except:
            pass
        
        print(f"\n📊 [STATS] Session Summary:")
        print(f"   • Total Blinks: {TOTAL_BLINKS} 👁️")
        print(f"   • Total Frames: {frame_count} 🎬")
        print("\n" + "🌟"*30)
        print("   Thanks for staying safe! You're a real one! 💯")
        print("   Catch you later bestie! ✌️😎")
        print("🌟"*30 + "\n")

if __name__ == "__main__":
    main()
