# 🚀 Quick Setup Guide

## System Overview
This is a **hybrid Python-Arduino system** that uses:
- **Arduino**: MQ-6 alcohol sensor + buzzer/LED control
- **Python + MediaPipe**: Webcam-based eye detection (no IR sensor needed!)

---

## ✅ Step-by-Step Installation

### 1️⃣ Hardware Setup (5 minutes)
Wire your components:
```
MQ-6 Sensor:  VCC → 5V,  GND → GND,  A0 → A0
Buzzer:       (+) → D8,   (-) → GND
LED:          (+) → 220Ω resistor → D7,  (-) → GND
Arduino:      Connect to PC via USB
```

### 2️⃣ Upload Arduino Code (2 minutes)
1. Open `AlcoholDrowsinessDetector.ino` in Arduino IDE
2. Select your board and COM port
3. Click **Upload**
4. Wait for "Done uploading"

### 3️⃣ Install Python Packages (5 minutes)
Open PowerShell in project folder:
```powershell
pip install -r requirements.txt
```

This installs:
- ✅ **opencv-python** - Camera handling
- ✅ **mediapipe** - Face/eye detection (Google's AI)
- ✅ **pyserial** - Arduino communication
- ✅ **numpy** - Math operations

**No CMake, no compilation, no manual downloads needed!**

### 4️⃣ Run the System
```powershell
python eye_detection.py
```

---

## 🎯 What You'll See

### On Your Screen:
- Live webcam feed with your face
- Green outlines around your eyes
- EAR (Eye Aspect Ratio) value in top-right
- "DROWSINESS ALERT!" warning when eyes close

### Console Output:
```
============================================================
Alcohol & Drowsiness Detection System - Eye Monitor
Powered by MediaPipe Face Mesh
============================================================

[INFO] Initializing MediaPipe Face Mesh...
[SUCCESS] MediaPipe initialized!
[SUCCESS] Arduino found on COM3
[SUCCESS] Connected to Arduino!
[SUCCESS] Camera started!

SYSTEM ACTIVE - Monitoring started
Press 'q' to quit
```

### When Alert Triggers:
- 🔊 **Buzzer beeps**
- 💡 **LED lights up**
- 🚨 **Screen shows warning**

---

## 🔧 Common Issues & Fixes

### "No module named 'cv2'"
```powershell
pip install opencv-python
```

### "No module named 'mediapipe'"
```powershell
pip install mediapipe
```

### "Could not connect to Arduino"
- Close Arduino Serial Monitor (only one program can use port!)
- Check Device Manager for COM port number
- Manually enter port when prompted

### "Could not open camera"
- Close other apps using webcam (Zoom, Teams, etc.)
- Try changing camera: Edit `eye_detection.py`, line with `cv2.VideoCapture(0)` → change `0` to `1`

### "No Face Detected"
- Improve lighting
- Face the camera directly
- Remove glasses if they're reflective
- Move closer to camera

### False Alarms (Too Sensitive)
Edit `eye_detection.py`:
```python
EYE_AR_THRESH = 0.20  # Increase to 0.22 or 0.25
EYE_AR_CONSEC_FRAMES = 48  # Increase to 60 or 72
```

---

## 📊 How It Works

```
┌─────────────┐         ┌──────────────┐
│   Webcam    │────────▶│   Python     │
│             │         │  MediaPipe   │
└─────────────┘         └──────┬───────┘
                               │
                        Detects eyes
                        closed > 2 sec
                               │
                               ▼
                        Sends 'E' command
                               │
                               ▼
┌─────────────┐      Serial   ┌──────────────┐
│   MQ-6      │────────────▶  │   Arduino    │
│  Sensor     │   Alcohol>400 │              │
└─────────────┘               └──────┬───────┘
                                     │
                              Activates alert
                                     │
                    ┌────────────────┴────────────────┐
                    ▼                                 ▼
            ┌───────────────┐              ┌──────────────┐
            │    Buzzer     │              │     LED      │
            │   (Beeps)     │              │  (Lights)    │
            └───────────────┘              └──────────────┘
```

---

## 🎓 Understanding EAR (Eye Aspect Ratio)

```
     p2   p3
      *   *        EAR = (||p2-p6|| + ||p3-p5||) / (2 * ||p1-p4||)
   *         *
p1 *    👁️    * p4    Eyes Open:   EAR ≈ 0.25-0.30
   *         *        Eyes Closed: EAR ≈ 0.10-0.15
      *   *
     p5   p6
```

When EAR drops below threshold (0.20) for 2 seconds → ALERT!

---

## 📝 Files You Can Delete

Since we switched to MediaPipe, you can **delete**:
- ❌ `shape_predictor_68_face_landmarks.dat` (was for dlib)
- ❌ Any `.bz2` files

MediaPipe downloads its own models automatically!

---

## 🎮 Controls

- **'q' key** - Quit application
- **Ctrl+C** - Force stop (in terminal)

---

## 🔥 Pro Tips

1. **Best lighting**: Bright, even light on your face
2. **Camera position**: Eye level, 1-2 feet away
3. **Testing alcohol sensor**: Breathe near sensor or use hand sanitizer
4. **Calibration**: Watch EAR values for a minute to understand your baseline

---

## ⚠️ Important Safety Note

**This is an educational/prototype project!**
- ❌ Do NOT rely on this for actual driving safety
- ❌ Not a substitute for certified breathalyzers
- ❌ Always follow traffic laws
- ⚠️ Never drive under the influence

---

## 📞 Need Help?

Check `README.md` for detailed documentation and troubleshooting!

---

**Made with ❤️ using MediaPipe, Arduino, and OpenCV**
