# Quick Start Guide - Production Drowsiness & Alcohol Detection System v3.0

## ⚡ 30-Second Setup

### 1. **Install Dependencies (Windows)**
```powershell
# Make sure Python 3.12+ is installed
python --version

# Install all packages
pip install -r requirements.txt
```

### 2. **Upload Arduino Firmware**
- Open Arduino IDE
- Load: `AlcoholDrowsinessDetector.ino`
- Select Board: Arduino Uno
- Select Port: COM3 (or your device)
- Click Upload
- Wait for "SYSTEM_READY" in Serial Monitor

### 3. **Run Python Application**
```powershell
python3 eye_detection.py
```

---

## 🎬 What to Expect

### Phase 1: Calibration (2 seconds)
```
========================================
   SYSTEM READY - CALIBRATION PHASE STARTING
   Please keep your face in view. Do not blink or yawn.
========================================

CALIBRATION PHASE
Progress: ████░░░░░░░░░░ 45%
```
✅ Keep your face steady, natural eye position
✅ Let the system scan your baseline EAR/MAR values

### Phase 2: Live Monitoring (Continuous)
```
THREAT: 23.5/100
Type: DROWSY
EAR: 0.2847 (Thresh: 0.2100)
FPS: 29.8
Alcohol: 287
Drowsy: 0 frames | Yawns: 0
Arduino: Connected
```

### Phase 3: Alert Generation (If Threat Detected)
```
[ALERT] Threat Score: 67.3/100 | Type: DROWSY
[ALERT] EAR: 0.1546 (Baseline: 0.2847)
[ALERT] MAR: 0.0521
[ALERT] Alcohol Level: 287

[RELAY] *** ENGINE KILL-SWITCH ACTIVATED *** (if score >75)
```

---

## 🔌 Hardware Wiring Diagram

```
Arduino Uno
============

  A0 -------- MQ-3 Sensor (A0 pin)
  D7 -------- Status LED (→ GND through 220Ω resistor)
  D8 -------- Buzzer Positive (→ GND for negative)
  D9 -------- Relay Module IN pin (→ GND for common)
  GND ------- Common ground (Arduino, sensor, buzzer, relay)
  5V -------- VCC for sensor and relay module

Relay Module (5V)
=================
  IN ---- D9 (Arduino)
  GND --- Arduino GND
  VCC --- 5V power
  Relay COM --- Car ignition wire (to cut)
  Relay NO/NC --- Switch based on signal


MQ-3 Alcohol Sensor
===================
  VCC --- 5V
  GND --- Arduino GND
  A0 ---- Arduino A0 (analog input)
```

---

## ⌨️ Keyboard Controls (While Running)

| Key | Action |
|---|---|
| **Q** | Quit application cleanly |
| **S** | Save screenshot (JPEG) |
| (Screenshots auto-save to working directory) |

---

## 📊 Telemetry Database Query Examples

### View Last 10 Alerts
```powershell
# Open PowerShell and navigate to project folder
sqlite3 telemetry.db "SELECT timestamp, threat_score, trigger_reason FROM alerts ORDER BY timestamp DESC LIMIT 10;"
```

### Export to CSV
```powershell
sqlite3 telemetry.db ".headers on" ".mode csv" "SELECT * FROM alerts;" > alerts_export.csv
```

### Get Statistics
```powershell
sqlite3 telemetry.db "SELECT trigger_reason, COUNT(*), AVG(threat_score) FROM alerts GROUP BY trigger_reason;"
```

---

## 🚨 Common Issues & Fixes

### Issue: "MediaPipe: attribute 'solutions' not found"
**Cause:** Python 3.14 has breaking changes with MediaPipe 0.10.33
**Fix:** Use Python 3.12
```powershell
py --list-paths  # Check available Python versions
# Download Python 3.12 if not available
```

### Issue: Arduino Port Not Found
**Cause:** USB driver not installed or wrong port
**Fix:**
1. Install [CH340 driver](https://github.com/WCHSoftware/CH34xInstallTool)
2. Check Device Manager for COM port number
3. Edit Python code to manually specify: `arduino.connect("COM3")`

### Issue: "No Face Detected" - Constant message
**Cause:** Poor lighting or face too far
**Fix:**
- Increase room lighting
- Position face 12-18 inches from webcam
- Clean camera lens
- Adjust CAMERA_INDEX in Config to 1 or 2

### Issue: False Positive Alerts (Too Sensitive)
**Cause:** Calibration with blink or yawn
**Fix:**
- Restart application
- During calibration phase, keep eyes COMPLETELY open
- Don't yawn or blink - static eye position for 2 seconds

### Issue: Relay Won't Activate
**Cause:** Threat score not reaching 75, or relay wiring issue
**Fix:**
1. Verify threat score reaches 75+ (check console output)
2. Test relay with continuity meter
3. Verify 5V power on relay module
4. Check D9 pin for proper wiring

---

## 📈 Performance Tips

### Get Better Accuracy
```python
# In Config class (eye_detection.py):
CALIBRATION_FRAMES = 100   # More samples = more robust
EAR_BUFFER_SIZE = 10       # Smoother EAR readings
```

### Speed Up Response Time
```python
EAR_CONSECUTIVE_FRAMES = 20   # Faster alert generation (1 sec @ 30 FPS instead of 2)
THREAT_SCORE_WARNING = 40     # Lower alert threshold
```

### Extend Relay Hold Time
```cpp
// In Arduino firmware:
#define RELAY_AUTO_RESET_TIME 10000  // 10 seconds instead of 5
```

---

## 🔄 System Update Flow

```
┌─────────────────────────────────────┐
│  Python Starts                      │
└────────────┬────────────────────────┘
             │
1. Initialize MediaPipe
2. Open SQLite database
3. Create video capture thread
             │
             ▼
┌─────────────────────────────────────┐
│  Connect to Arduino                 │
│  - Auto-detect COM port             │
│  - Or manual entry                  │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│  Calibration Phase (50 frames)      │
│  - Baseline EAR/MAR from user       │
│  - Stored in memory                 │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│  Live Monitoring Loop               │
│  - Read frame from queue            │
│  - Detect face landmarks            │
│  - Calculate EAR/MAR/Threat         │
│  - Send to Arduino if alert         │
│  - Log to SQLite if threshold hit   │
│  - Display on screen                │
│  - Loop until user presses Q        │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│  Graceful Shutdown                  │
│  - Stop video thread                │
│  - Close Arduino connection         │
│  - Close database                   │
│  - Release OpenCV resources         │
└─────────────────────────────────────┘
```

---

## 🎯 Real-World Usage Scenario

### Driver Monitoring System
1. **Driver enters car** → System starts
2. **Calibration phase** → Driver's baseline established (2 sec)
3. **Normal driving** → Threat score stays <50, green display
4. **Driver gets tired** → Eyes close for 1+ seconds
   - Threat score jumps to 45
   - Buzzer plays pattern: `BEEP───` (500ms tone, 1.5s cycle)
5. **Driver drinks** → Arduino detects alcohol vapor (ADC >400)
   - Threat multiplier activates
   - Same drowsiness now scores 65 instead of 45
6. **Critical situation** → Eyes closed + Alcohol detected
   - Threat score **75+** → CRITICAL alert
   - Relay energizes → Engine ignition circuit cut
   - Buzzer pattern: Rapid `BEEP-BEEP-BEEP` (100ms pulses)
   - System logs: timestamp, threat=78, trigger="MULTI", duration=8.3s

---

## 📞 Support

### Check System Status
```powershell
# Verify Python environment
python -c "import cv2, mediapipe, numpy; print('All dependencies OK')"

# Check Arduino connection
# (Arduino IDE Serial Monitor should show "SYSTEM_READY")

# Verify database
sqlite3 telemetry.db ".tables"  # Should list: alerts, calibration
```

### Debug Mode
Add to Python code at start of `main()`:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## ✅ Success Checklist

- [ ] Python 3.12+ installed
- [ ] All dependencies installed (`pip install -r requirements.txt`)
- [ ] Arduino uploaded with latest firmware
- [ ] USB cable connected (Arduino shows COM port)
- [ ] Webcam working (test in Windows camera app)
- [ ] MQ-3 sensor wired to A0
- [ ] Buzzer wired to D8
- [ ] Relay wired to D9
- [ ] SQLite database created (first run)
- [ ] Calibration completed successfully
- [ ] System monitoring in real-time

---

## 🚀 You're Ready!

Press Enter and run:
```powershell
python3 eye_detection.py
```

The system will:
1. ✅ Automatically detect Arduino
2. ✅ Calibrate to your baseline
3. ✅ Start real-time monitoring
4. ✅ Log all alerts to database
5. ✅ Control relay on critical threat

---

**System Version:** 3.0 Production-Grade  
**Python:** 3.12+  
**Arduino:** Uno/Nano  
**Last Updated:** March 2026
