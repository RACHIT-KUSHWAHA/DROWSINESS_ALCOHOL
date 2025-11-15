# 🚗 Alcohol & Drowsiness Detection System# Alcohol and Drowsiness Detection System



<div align="center">A hybrid Python-Arduino safety system that monitors driver alertness through camera-based eye closure detection and alcohol level monitoring using an MQ-6 gas sensor.



![Status](https://img.shields.io/badge/Status-Active-success)## Features

![Version](https://img.shields.io/badge/Version-2.0-blue)

![Python](https://img.shields.io/badge/Python-3.7+-yellow)- **Camera-Based Drowsiness Detection**: Uses laptop webcam with Google MediaPipe Face Mesh for accurate eye tracking

![Arduino](https://img.shields.io/badge/Arduino-Compatible-green)- **Eye Aspect Ratio (EAR) Algorithm**: Detects if eyes are closed for more than 2 seconds using 478 facial landmarks

![License](https://img.shields.io/badge/License-Open_Source-orange)- **Alcohol Detection**: Monitors alcohol levels via MQ-6 sensor, triggers alert if level exceeds 400

- **Dual Alert System**: Activates both buzzer and LED when either condition is detected

**A hybrid Arduino-Python safety system for real-time driver monitoring**- **Python-Arduino Communication**: Seamless serial communication between eye detection script and hardware

- **Real-time Monitoring**: Live video feed with EAR values and visual feedback

[Features](#-features) • [Quick Start](#-quick-start) • [Documentation](#-documentation) • [Demo](#-demo) • [Support](#-support)

## Components Required

</div>

### Hardware

---| Component | Quantity | Specification |

|-----------|----------|---------------|

## 📋 Overview| Arduino Uno/Nano | 1 | Any Arduino board |

| MQ-6 Gas Sensor | 1 | LPG/Alcohol sensor |

The **Alcohol & Drowsiness Detection System** is an innovative safety solution that combines hardware sensors with advanced computer vision to monitor driver alertness. Using Google's MediaPipe Face Mesh for eye tracking and an MQ-6 sensor for alcohol detection, the system provides real-time alerts when dangerous conditions are detected.| Buzzer | 1 | Active buzzer (5V) |

| LED | 1 | Any color (5mm recommended) |

### 🎯 Key Highlights| Resistor | 1 | 220Ω (for LED) |

| Breadboard | 1 | For prototyping |

- **Real-time Eye Tracking**: 478 facial landmarks with MediaPipe Face Mesh| Jumper Wires | Several | Male-to-male, male-to-female |

- **Eye Aspect Ratio (EAR) Algorithm**: Detects prolonged eye closure (>2 seconds)

- **Alcohol Monitoring**: MQ-6 gas sensor with configurable threshold (default: 400)### Software

- **Dual Alert System**: Visual and audible warnings via LED and buzzer| Software | Purpose |

- **Serial Communication**: Seamless Python-Arduino integration|----------|---------|

- **Live Video Feed**: Real-time monitoring with visual overlays| Arduino IDE | For uploading code to Arduino |

| Python 3.7+ | For running eye detection script |

---| Laptop with Webcam | For capturing face/eye images |



## ✨ Features## Circuit Connections



### 🎥 Vision-Based Drowsiness Detection### MQ-6 Alcohol Sensor

- Uses laptop webcam (no additional IR sensors required)```

- MediaPipe Face Mesh: 478 facial landmarks for precise trackingMQ-6 VCC  →  Arduino 5V

- Calculates Eye Aspect Ratio (EAR) for both eyesMQ-6 GND  →  Arduino GND

- Configurable threshold and duration parametersMQ-6 A0   →  Arduino A0

- Blink counter and FPS display```



### 🍺 Alcohol Level Monitoring### Buzzer

- MQ-6 LPG/Alcohol gas sensor```

- Analog reading (0-1023 range)Buzzer (+)  →  Arduino D8

- Adjustable threshold levelsBuzzer (-)  →  Arduino GND

- Continuous monitoring with 100ms sampling rate```

- Auto-calibration during 20-second warmup

### LED

### 🚨 Alert System```

- **Buzzer**: Audible alarm with 500ms pulse patternLED Anode (+)  →  220Ω Resistor  →  Arduino D7

- **LED**: Visual indicator with synchronized pulsingLED Cathode (-) →  Arduino GND

- **Screen Overlay**: "DROWSINESS ALERT" banner on video feed```

- **Serial Logging**: Detailed console output for debugging

## Wiring Diagram (Text Format)

### 🔌 Connectivity

- Automatic Arduino port detection```

- Robust serial communication (9600 baud)                    Arduino Uno

- Command protocol: 'E' (eyes closed), 'N' (normal)                   ┌─────────┐

- Real-time data exchange                   │         │

    MQ-6 A0 ───────┤ A0      │

---                   │         │

                   │ USB ────┼──── Connected to Computer (Python Script)

## 🛠️ Hardware Requirements                   │         │

                   │     D7  ├───── 220Ω ───── LED (+) → GND

| Component | Specification | Quantity | Purpose |                   │         │

|-----------|--------------|----------|---------|                   │     D8  ├───── Buzzer (+) → GND

| **Arduino Uno/Nano** | ATmega328P | 1 | Main controller |                   │         │

| **MQ-6 Gas Sensor** | LPG/Alcohol sensor | 1 | Alcohol detection |    5V ────────────┤ 5V      │──── MQ-6 VCC

| **Buzzer** | Active 5V | 1 | Audible alarm |                   │         │

| **LED** | 5mm, any color | 1 | Visual indicator |    GND ───────────┤ GND     │──── All GND connections

| **Resistor** | 220Ω | 1 | LED current limiting |                   │         │

| **Breadboard** | 400-830 points | 1 | Prototyping |                   └─────────┘

| **Jumper Wires** | Male-to-male | ~10 | Connections |                        ↕

| **USB Cable** | Type A to B | 1 | Arduino-PC link |                  Serial Communication

| **Webcam** | Integrated or USB | 1 | Eye detection |                        ↕

              ┌─────────────────┐

### 💻 Software Requirements              │   Computer      │

              │  Python Script  │

- **Arduino IDE** 1.8.x or 2.x              │  + Webcam       │

- **Python** 3.7 or higher              └─────────────────┘

- **Operating System**: Windows 10/11, macOS 10.15+, Linux (Ubuntu 18.04+)```



### 📦 Python Dependencies## Installation Steps



```### 1. Hardware Setup

opencv-python >= 4.5.01. Connect all components according to the circuit diagram above

mediapipe >= 0.10.02. Double-check all connections, especially power (5V) and ground (GND)

pyserial >= 3.53. Ensure the 220Ω resistor is connected in series with the LED

numpy >= 1.19.04. Connect Arduino to computer via USB cable

```

### 2. Arduino Software Setup

---1. Install [Arduino IDE](https://www.arduino.cc/en/software) if not already installed

2. Open `AlcoholDrowsinessDetector.ino` in Arduino IDE

## 🚀 Quick Start3. Select your Arduino board: `Tools → Board → Arduino Uno` (or your model)

4. Select the correct COM port: `Tools → Port → COMx` (note this port for Python script)

### Step 1: Hardware Setup ⚡5. Click **Upload** button to upload the code to Arduino

6. Arduino will warm up MQ-6 sensor for 20 seconds

```

MQ-6 Sensor          Arduino Uno### 3. Python Environment Setup

━━━━━━━━━━          ━━━━━━━━━━━1. Install Python 3.7 or higher from [python.org](https://www.python.org/downloads/)

VCC ───────────────→ 5V2. Open Command Prompt/Terminal in the project folder

GND ───────────────→ GND3. Install required Python packages:

A0  ───────────────→ A0   ```bash

   pip install -r requirements.txt

Buzzer               Arduino Uno   ```

━━━━━━               ━━━━━━━━━━━   **Note**: MediaPipe will automatically download required models on first run (no manual downloads needed!)

(+) ───────────────→ D8

(-) ───────────────→ GND### 4. Running the System

1. **Keep Arduino connected** to computer via USB

LED                  Arduino Uno2. **Do NOT** open Arduino Serial Monitor (it will block Python communication)

━━━                  ━━━━━━━━━━━3. Run the Python script:

Anode (+) ─→ 220Ω ─→ D7   ```bash

Cathode (-) ────────→ GND   python eye_detection.py

```   ```

4. The script will automatically detect Arduino port and connect

### Step 2: Arduino Upload 📤5. Position yourself in front of the webcam

6. System will display live feed with eye detection overlay

1. Open `AlcoholDrowsinessDetector.ino` in Arduino IDE7. Press **'q'** to quit the application

2. Select board: **Tools → Board → Arduino Uno**

3. Select port: **Tools → Port → COMx** (Windows) or **/dev/ttyUSBx** (Linux)### 5. Initial Calibration

4. Click **Upload** (Ctrl+U)1. Observe the EAR (Eye Aspect Ratio) value displayed on video feed

5. Wait for "Done uploading" message2. Normal open eyes: EAR ≈ 0.20-0.30 (MediaPipe values)

3. Closed eyes: EAR ≈ 0.10-0.15

### Step 3: Python Setup 🐍4. Adjust `EYE_AR_THRESH` in `eye_detection.py` if needed (default: 0.20)



```powershell## How It Works

# Clone or download the project

cd AlcoholDrowsinessDetector### Drowsiness Detection (Python + MediaPipe)

1. Webcam captures real-time video feed

# Install dependencies2. **Google MediaPipe Face Mesh** detects face and extracts 478 facial landmarks

pip install -r requirements.txt3. Eye landmarks are extracted and Eye Aspect Ratio (EAR) is calculated for both eyes:

   - `EAR = (||p2-p6|| + ||p3-p5||) / (2 * ||p1-p4||)`

# Verify installation4. When EAR drops below threshold (0.20) for 48 consecutive frames (~2 seconds):

python -c "import cv2, mediapipe, serial; print('All modules installed!')"   - Python sends **'E'** command to Arduino via serial

```   - Arduino activates buzzer and LED

5. When eyes reopen:

### Step 4: Run the System ▶️   - Python sends **'N'** command to Arduino

   - Arduino deactivates alert (if no alcohol detected)

```powershell

python eye_detection.py### Alcohol Detection (Arduino + MQ-6)

```- MQ-6 sensor continuously reads analog values (0-1023)

- When reading exceeds **400**, the alert activates

**Important**: Close Arduino Serial Monitor before running Python script!- Alert remains active until alcohol level drops below threshold



---### Alert Mechanism

- **Either** condition triggers both buzzer and LED

## 🎮 Demo- Buzzer produces audible alarm

- LED provides visual indication

### System Startup- Alerts remain active until both conditions clear

```

============================================================### Communication Protocol

   ALCOHOL & DROWSINESS DETECTION SYSTEM- **Python → Arduino**:

   Eye Monitoring Module - Powered by MediaPipe  - `'E'` = Eyes closed (drowsiness detected)

============================================================  - `'N'` = Eyes open (normal)

- **Arduino → Python**:

[INFO] Initializing MediaPipe Face Mesh...  - `"ALERT:DROWSY"` = Drowsiness alert active

[SUCCESS] MediaPipe initialized successfully  - `"ALERT:ALCOHOL"` = Alcohol alert active

  - `"ALERT:BOTH"` = Both alerts active

[INFO] Searching for Arduino...

[SUCCESS] Arduino detected on COM3## Calibration & Adjustment

[SUCCESS] Serial connection established

### Adjusting Eye Closure Time

[INFO] Waiting for Arduino initialization...In `eye_detection.py`, modify this line:

[ARDUINO] ========================================```python

[ARDUINO]   ALCOHOL & DROWSINESS DETECTIONEYE_AR_CONSEC_FRAMES = 48  # Number of frames (~2 sec at 24 fps)

[ARDUINO]      Arduino Controller v2.0```

[ARDUINO] ========================================

[ARDUINO] SYSTEM_READY### Adjusting Eye Aspect Ratio Threshold

In `eye_detection.py`, modify:

[INFO] Initializing camera...```python

[SUCCESS] Camera initialized successfullyEYE_AR_THRESH = 0.20  # Lower = more sensitive to closure (MediaPipe optimized)

```

============================================================

   SYSTEM ACTIVE - Monitoring Started### Adjusting Alcohol Threshold

============================================================In the code, modify this line:

``````cpp

#define ALCOHOL_THRESHOLD 400  // Change value (0-1023)

### Live Monitoring```

- **Video Window**: Real-time webcam feed with green eye contours

- **EAR Display**: Current Eye Aspect Ratio value (top-right)

- **Status Indicators**: FPS, Arduino connection, alcohol level (bottom-left)

- **Alert Banner**: Red "DROWSINESS ALERT" when eyes close >2 seconds## Troubleshooting



### Keyboard Controls### Python Script Issues

| Key | Action |

|-----|--------|#### "Could not connect to Arduino"

| **Q** | Quit application |- Close Arduino Serial Monitor if open

| **R** | Reset blink counter |- Check Arduino is connected via USB

| **S** | Save screenshot |- Manually enter COM port when prompted

- Check `Device Manager` (Windows) to verify COM port

---

#### "Could not open camera"

## 📊 How It Works- Check if another application is using webcam

- Try different camera index: change `cv2.VideoCapture(0)` to `(1)` or `(2)`

### Eye Aspect Ratio (EAR) Algorithm- Test webcam with other applications



```#### "No Face Detected"

      p2   p3- Ensure adequate lighting

       ●   ●        EAR = (||p2-p6|| + ||p3-p5||) / (2 × ||p1-p4||)- Position face clearly in front of camera

    ●         ●- Try adjusting distance from camera

 p1 ●    👁️    ● p4    - Check if face is fully visible (no obstructions)

    ●         ●     • Eyes Open:   EAR ≈ 0.25-0.30

       ●   ●        • Eyes Closed: EAR ≈ 0.10-0.15### Arduino Issues

      p5   p6       • Threshold:   EAR < 0.20

```#### Buzzer/LED Always On

- Check MQ-6 sensor readings (visible in Python script output)

### System Workflow- Sensor may need more warm-up time (up to 48 hours for accurate readings)

- Adjust `ALCOHOL_THRESHOLD` in Arduino code to higher value

```

┌─────────┐         ┌──────────┐         ┌─────────┐#### No Communication Between Python and Arduino

│ Webcam  │────────→│MediaPipe │────────→│   EAR   │- Ensure Arduino Serial Monitor is **CLOSED**

└─────────┘         └──────────┘         │  Calc   │- Only one program can access serial port at a time

                                         └────┬────┘- Verify baud rate is 9600 in both Python and Arduino code

                                              │- Try unplugging and replugging USB cable

                                         EAR < 0.20

                                         for 2 sec### False Alarms

                                              │

                                              ▼#### Drowsiness False Positives

                                     ┌────────────────┐- Increase `EYE_AR_CONSEC_FRAMES` for longer detection time

                                     │ Python Script  │- Adjust `EYE_AR_THRESH` (higher = less sensitive)

                                     └────────┬───────┘- Ensure good lighting on face

                                              │- Avoid glasses with reflective lenses

                                       Serial: 'E'/'N'

                                              │#### Alcohol False Positives

┌─────────┐         ┌──────────┐            │- MQ-6 needs proper warm-up (20-30 seconds minimum)

│  MQ-6   │────────→│ Arduino  │◄───────────┘- Sensor may detect environmental gases (cooking, cleaning products)

│ Sensor  │  Level  └─────┬────┘- Increase `ALCOHOL_THRESHOLD` value

└─────────┘   >400        │- Allow sensor to stabilize in clean air

                          │

                          ▼## System Output Examples

                  ┌───────────────┐

                  │ Alert System  │### Python Console Output

                  └───┬───────┬───┘```

                      │       │============================================================

                  ┌───▼───┐ ┌─▼───┐Alcohol & Drowsiness Detection System - Eye Monitor

                  │Buzzer │ │ LED │Powered by MediaPipe Face Mesh

                  └───────┘ └─────┘============================================================

```

[INFO] Initializing MediaPipe Face Mesh...

### Communication Protocol[SUCCESS] MediaPipe initialized!



| Direction | Command | Description |[INFO] Searching for Arduino...

|-----------|---------|-------------|[SUCCESS] Arduino found on COM3

| Python → Arduino | `'E'` | Eyes closed (drowsiness detected) |

| Python → Arduino | `'N'` | Eyes open (normal state) |[INFO] Starting camera...

| Python → Arduino | `'S'` | Status request |[SUCCESS] Camera started!

| Arduino → Python | `"Level = X"` | Current alcohol level |

| Arduino → Python | `"ALERT:DROWSY"` | Drowsiness alert active |============================================================

| Arduino → Python | `"ALERT:ALCOHOL"` | Alcohol alert active |SYSTEM ACTIVE - Monitoring started

Press 'q' to quit

---============================================================



## ⚙️ Configuration[ALERT] DROWSINESS DETECTED! EAR: 0.18

[ARDUINO] ALERT:DROWSY

### Adjust Drowsiness Sensitivity[INFO] Eyes open - Normal state

```

Edit `eye_detection.py`:

### Video Feed Display

```python- Live webcam feed with green eye contours

# Make less sensitive (require more eye closure)- EAR value displayed in real-time

EYE_AR_THRESH = 0.25        # Default: 0.20- Frame counter showing closed duration

- "DROWSINESS ALERT!" warning when triggered

# Increase detection time

EYE_AR_CONSEC_FRAMES = 72   # Default: 48 (~3 seconds instead of 2)## Safety Notes

```

⚠️ **Important Warnings:**

### Adjust Alcohol Threshold- This is a **prototype/educational project**, not certified safety equipment

- Do NOT rely on this as sole safety measure for driving

Edit `AlcoholDrowsinessDetector.ino`:- MQ-6 sensors require calibration and may not be legally accurate

- Always follow traffic laws and drive responsibly

```cpp- Never drive under the influence of alcohol

// Change threshold (0-1023)- Consult professional safety equipment for real-world applications

#define ALCOHOL_THRESHOLD 500  // Default: 400

```## Enhancements & Future Improvements



### Change Camera Index- Add LCD display for visual feedback

- Implement data logging to SD card

Edit `eye_detection.py`:- Add WiFi module for remote monitoring

- Use camera-based eye detection with OpenCV

```python- Add GPS module for location tracking

CAMERA_INDEX = 1  # Try 1 or 2 if default camera doesn't work- Implement multiple sensitivity levels

```- Add smartphone app integration via Bluetooth



---## Project Structure



## 🐛 Troubleshooting```

AlcoholDrowsinessDetector/

<details>├── AlcoholDrowsinessDetector.ino    # Arduino sketch (alcohol + alert control)

<summary><b>❌ "Could not connect to Arduino"</b></summary>├── eye_detection.py                  # Python script (MediaPipe eye detection)

├── requirements.txt                  # Python dependencies

**Solutions:**└── README.md                         # This file

- Close Arduino Serial Monitor (only one program can access COM port)```

- Check Device Manager (Windows) or `ls /dev/tty*` (Linux) for correct port

- Manually enter COM port when prompted## Code Structure

- Try unplugging and replugging USB cable

- Ensure Arduino code is uploaded successfully### Arduino (`AlcoholDrowsinessDetector.ino`)

</details>- `setup()`: Initializes pins, serial communication, and sensor warm-up

- `loop()`: Main monitoring loop (checks serial and MQ-6 sensor)

<details>- `activateAlert()`: Turns on buzzer and LED

<summary><b>❌ "Could not open camera"</b></summary>- `deactivateAlert()`: Turns off buzzer and LED



**Solutions:**### Python (`eye_detection.py`)

- Close other applications using webcam (Zoom, Teams, Skype)- `eye_aspect_ratio()`: Calculates EAR from MediaPipe eye landmarks

- Change `CAMERA_INDEX` to 1 or 2 in `eye_detection.py`- `get_eye_landmarks()`: Extracts eye coordinates from MediaPipe Face Mesh

- Check camera permissions in OS settings- `find_arduino_port()`: Auto-detects Arduino COM port

- Test webcam with other software (e.g., Windows Camera app)- `main()`: Main loop for camera capture, MediaPipe face detection, and Arduino communication

</details>

## License

<details>

<summary><b>❌ "No Face Detected"</b></summary>This project is open-source and available for educational purposes.



**Solutions:**## Author

- Improve lighting conditions

- Position face directly in front of cameraCreated for Arduino-based driver safety monitoring system.

- Maintain 1-2 feet distance from camera

- Remove reflective glasses or sunglasses---

- Ensure face is fully visible (no obstructions)

</details>**Last Updated:** October 2025


<details>
<summary><b>❌ "No module named 'cv2'"</b></summary>

**Solution:**
```powershell
pip install opencv-python mediapipe pyserial numpy
```
</details>

<details>
<summary><b>⚠️ False Alarms (Too Sensitive)</b></summary>

**Solutions:**
- Increase `EYE_AR_THRESH` to 0.22-0.25
- Increase `EYE_AR_CONSEC_FRAMES` to 60-72
- Improve face lighting
- Adjust camera angle to face level
</details>

<details>
<summary><b>⚠️ Buzzer/LED Always On</b></summary>

**Solutions:**
- Allow MQ-6 sensor full warmup (20-30 seconds)
- Increase `ALCOHOL_THRESHOLD` in Arduino code
- Check sensor readings in Serial Monitor
- Ensure sensor is in clean air environment
</details>

---

## 📖 Documentation

- **[TECHNICAL_SPECS.md](TECHNICAL_SPECS.md)** - Detailed technical specifications
- **[Arduino Code](AlcoholDrowsinessDetector.ino)** - Fully commented firmware
- **[Python Code](eye_detection.py)** - Documented detection script

---

## 🔒 Safety & Legal Disclaimer

> ⚠️ **IMPORTANT**: This project is designed for **educational and prototyping purposes only**.

- ❌ **NOT** a replacement for certified breathalyzer devices
- ❌ **NOT** suitable for legal alcohol testing
- ❌ **NOT** certified for automotive safety applications
- ❌ **DO NOT** rely on this system for driving safety decisions
- ✅ Always follow local traffic laws and regulations
- ✅ Never drive under the influence of alcohol
- ✅ Consult professional safety equipment for real-world use

---

## 🎯 Future Enhancements

- [ ] LCD display for standalone operation
- [ ] SD card logging for data analysis
- [ ] GPS module for location tracking
- [ ] Smartphone app via Bluetooth
- [ ] Multiple driver profiles
- [ ] Cloud data synchronization
- [ ] Advanced ML models for emotion detection
- [ ] Temperature and humidity compensation for MQ-6

---

## 📜 License

This project is open-source and available under the MIT License.

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

---

## 💬 Support

- 📧 **Issues**: [GitHub Issues](https://github.com/RACHIT-KUSHWAHA/DROWSINESS_ALCOHOL/issues)
- 📖 **Documentation**: See `TECHNICAL_SPECS.md`
- 💡 **Questions**: Create a discussion in the repository

---

## 👏 Acknowledgments

- **Google MediaPipe** - Face mesh detection
- **OpenCV** - Computer vision processing
- **Arduino Community** - Hardware support
- **Python Community** - Libraries and tools

---

<div align="center">

**Made with ❤️ for road safety**

⭐ Star this repo if you find it helpful!

</div>
