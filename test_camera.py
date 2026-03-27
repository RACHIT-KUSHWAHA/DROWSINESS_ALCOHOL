"""
Quick camera test script to find and verify your laptop camera.
"""

import cv2
import time

print("\n" + "="*70)
print("   CAMERA DETECTION TEST")
print("="*70 + "\n")

# Try different camera indices
for camera_index in range(0, 5):
    print(f"[TEST] Trying camera index {camera_index}...")
    cap = cv2.VideoCapture(camera_index)
    
    if not cap.isOpened():
        print(f"  ❌ Camera {camera_index} not available")
        continue
    
    # Try to read a frame
    ret, frame = cap.read()
    
    if ret and frame is not None:
        h, w = frame.shape[:2]
        print(f"  ✓ Camera {camera_index} WORKS!")
        print(f"    Resolution: {w}x{h}")
        print(f"    Frame shape: {frame.shape}")
        
        # Display camera feed for 3 seconds
        print(f"\n  [Press 'q' to skip, or wait 3 seconds...]")
        start_time = time.time()
        
        while time.time() - start_time < 3:
            ret, frame = cap.read()
            if ret:
                cv2.imshow(f"Camera {camera_index} Preview", frame)
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
        
        cv2.destroyAllWindows()
        
        print(f"\n  UPDATE your eye_detection.py:")
        print(f"    Find this line: CAMERA_INDEX = 0")
        print(f"    Change it to: CAMERA_INDEX = {camera_index}")
        print(f"\n  Then run: python eye_detection.py\n")
        
        cap.release()
        break
    else:
        print(f"  ❌ Could not read frame from camera {camera_index}")
        cap.release()

print("="*70)
print("If no camera was found, try these troubleshooting steps:")
print("1. Check Device Manager - camera should be listed under Imaging devices")
print("2. Restart your laptop")
print("3. Check if camera is already in use by another app (Teams, Zoom, etc.)")
print("4. Try closing and reopening the test script")
print("="*70 + "\n")
