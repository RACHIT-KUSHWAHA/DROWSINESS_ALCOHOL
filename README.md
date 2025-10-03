# Alcohol and Drowsiness Detection System

A hybrid Python-Arduino safety system that monitors driver alertness through camera-based eye closure detection and alcohol level monitoring using an MQ-6 gas sensor.

## Features

- **Camera-Based Drowsiness Detection**: Uses laptop webcam with Google MediaPipe Face Mesh for accurate eye tracking
- **Eye Aspect Ratio (EAR) Algorithm**: Detects if eyes are closed for more than 2 seconds using 478 facial landmarks
- **Alcohol Detection**: Monitors alcohol levels via MQ-6 sensor, triggers alert if level exceeds 400
- **Dual Alert System**: Activates both buzzer and LED when either condition is detected
- **Python-Arduino Communication**: Seamless serial communication between eye detection script and hardware
- **Real-time Monitoring**: Live video feed with EAR values and visual feedback

## Components Required

### Hardware
| Component | Quantity | Specification |
|-----------|----------|---------------|
| Arduino Uno/Nano | 1 | Any Arduino board |
| MQ-6 Gas Sensor | 1 | LPG/Alcohol sensor |
| Buzzer | 1 | Active buzzer (5V) |
| LED | 1 | Any color (5mm recommended) |
| Resistor | 1 | 220Ω (for LED) |
| Breadboard | 1 | For prototyping |
| Jumper Wires | Several | Male-to-male, male-to-female |

### Software
| Software | Purpose |
|----------|---------|
| Arduino IDE | For uploading code to Arduino |
| Python 3.7+ | For running eye detection script |
| Laptop with Webcam | For capturing face/eye images |

## Circuit Connections

### MQ-6 Alcohol Sensor
```
MQ-6 VCC  →  Arduino 5V
MQ-6 GND  →  Arduino GND
MQ-6 A0   →  Arduino A0
```

### Buzzer
```
Buzzer (+)  →  Arduino D8
Buzzer (-)  →  Arduino GND
```

### LED
```
LED Anode (+)  →  220Ω Resistor  →  Arduino D7
LED Cathode (-) →  Arduino GND
```

## Wiring Diagram (Text Format)

```
                    Arduino Uno
                   ┌─────────┐
                   │         │
    MQ-6 A0 ───────┤ A0      │
                   │         │
                   │ USB ────┼──── Connected to Computer (Python Script)
                   │         │
                   │     D7  ├───── 220Ω ───── LED (+) → GND
                   │         │
                   │     D8  ├───── Buzzer (+) → GND
                   │         │
    5V ────────────┤ 5V      │──── MQ-6 VCC
                   │         │
    GND ───────────┤ GND     │──── All GND connections
                   │         │
                   └─────────┘
                        ↕
                  Serial Communication
                        ↕
              ┌─────────────────┐
              │   Computer      │
              │  Python Script  │
              │  + Webcam       │
              └─────────────────┘
```

## Installation Steps

### 1. Hardware Setup
1. Connect all components according to the circuit diagram above
2. Double-check all connections, especially power (5V) and ground (GND)
3. Ensure the 220Ω resistor is connected in series with the LED
4. Connect Arduino to computer via USB cable

### 2. Arduino Software Setup
1. Install [Arduino IDE](https://www.arduino.cc/en/software) if not already installed
2. Open `AlcoholDrowsinessDetector.ino` in Arduino IDE
3. Select your Arduino board: `Tools → Board → Arduino Uno` (or your model)
4. Select the correct COM port: `Tools → Port → COMx` (note this port for Python script)
5. Click **Upload** button to upload the code to Arduino
6. Arduino will warm up MQ-6 sensor for 20 seconds

### 3. Python Environment Setup
1. Install Python 3.7 or higher from [python.org](https://www.python.org/downloads/)
2. Open Command Prompt/Terminal in the project folder
3. Install required Python packages:
   ```bash
   pip install -r requirements.txt
   ```
   **Note**: MediaPipe will automatically download required models on first run (no manual downloads needed!)

### 4. Running the System
1. **Keep Arduino connected** to computer via USB
2. **Do NOT** open Arduino Serial Monitor (it will block Python communication)
3. Run the Python script:
   ```bash
   python eye_detection.py
   ```
4. The script will automatically detect Arduino port and connect
5. Position yourself in front of the webcam
6. System will display live feed with eye detection overlay
7. Press **'q'** to quit the application

### 5. Initial Calibration
1. Observe the EAR (Eye Aspect Ratio) value displayed on video feed
2. Normal open eyes: EAR ≈ 0.20-0.30 (MediaPipe values)
3. Closed eyes: EAR ≈ 0.10-0.15
4. Adjust `EYE_AR_THRESH` in `eye_detection.py` if needed (default: 0.20)

## How It Works

### Drowsiness Detection (Python + MediaPipe)
1. Webcam captures real-time video feed
2. **Google MediaPipe Face Mesh** detects face and extracts 478 facial landmarks
3. Eye landmarks are extracted and Eye Aspect Ratio (EAR) is calculated for both eyes:
   - `EAR = (||p2-p6|| + ||p3-p5||) / (2 * ||p1-p4||)`
4. When EAR drops below threshold (0.20) for 48 consecutive frames (~2 seconds):
   - Python sends **'E'** command to Arduino via serial
   - Arduino activates buzzer and LED
5. When eyes reopen:
   - Python sends **'N'** command to Arduino
   - Arduino deactivates alert (if no alcohol detected)

### Alcohol Detection (Arduino + MQ-6)
- MQ-6 sensor continuously reads analog values (0-1023)
- When reading exceeds **400**, the alert activates
- Alert remains active until alcohol level drops below threshold

### Alert Mechanism
- **Either** condition triggers both buzzer and LED
- Buzzer produces audible alarm
- LED provides visual indication
- Alerts remain active until both conditions clear

### Communication Protocol
- **Python → Arduino**:
  - `'E'` = Eyes closed (drowsiness detected)
  - `'N'` = Eyes open (normal)
- **Arduino → Python**:
  - `"ALERT:DROWSY"` = Drowsiness alert active
  - `"ALERT:ALCOHOL"` = Alcohol alert active
  - `"ALERT:BOTH"` = Both alerts active

## Calibration & Adjustment

### Adjusting Eye Closure Time
In `eye_detection.py`, modify this line:
```python
EYE_AR_CONSEC_FRAMES = 48  # Number of frames (~2 sec at 24 fps)
```

### Adjusting Eye Aspect Ratio Threshold
In `eye_detection.py`, modify:
```python
EYE_AR_THRESH = 0.20  # Lower = more sensitive to closure (MediaPipe optimized)
```

### Adjusting Alcohol Threshold
In the code, modify this line:
```cpp
#define ALCOHOL_THRESHOLD 400  // Change value (0-1023)
```



## Troubleshooting

### Python Script Issues

#### "Could not connect to Arduino"
- Close Arduino Serial Monitor if open
- Check Arduino is connected via USB
- Manually enter COM port when prompted
- Check `Device Manager` (Windows) to verify COM port

#### "Could not open camera"
- Check if another application is using webcam
- Try different camera index: change `cv2.VideoCapture(0)` to `(1)` or `(2)`
- Test webcam with other applications

#### "No Face Detected"
- Ensure adequate lighting
- Position face clearly in front of camera
- Try adjusting distance from camera
- Check if face is fully visible (no obstructions)

### Arduino Issues

#### Buzzer/LED Always On
- Check MQ-6 sensor readings (visible in Python script output)
- Sensor may need more warm-up time (up to 48 hours for accurate readings)
- Adjust `ALCOHOL_THRESHOLD` in Arduino code to higher value

#### No Communication Between Python and Arduino
- Ensure Arduino Serial Monitor is **CLOSED**
- Only one program can access serial port at a time
- Verify baud rate is 9600 in both Python and Arduino code
- Try unplugging and replugging USB cable

### False Alarms

#### Drowsiness False Positives
- Increase `EYE_AR_CONSEC_FRAMES` for longer detection time
- Adjust `EYE_AR_THRESH` (higher = less sensitive)
- Ensure good lighting on face
- Avoid glasses with reflective lenses

#### Alcohol False Positives
- MQ-6 needs proper warm-up (20-30 seconds minimum)
- Sensor may detect environmental gases (cooking, cleaning products)
- Increase `ALCOHOL_THRESHOLD` value
- Allow sensor to stabilize in clean air

## System Output Examples

### Python Console Output
```
============================================================
Alcohol & Drowsiness Detection System - Eye Monitor
Powered by MediaPipe Face Mesh
============================================================

[INFO] Initializing MediaPipe Face Mesh...
[SUCCESS] MediaPipe initialized!

[INFO] Searching for Arduino...
[SUCCESS] Arduino found on COM3

[INFO] Starting camera...
[SUCCESS] Camera started!

============================================================
SYSTEM ACTIVE - Monitoring started
Press 'q' to quit
============================================================

[ALERT] DROWSINESS DETECTED! EAR: 0.18
[ARDUINO] ALERT:DROWSY
[INFO] Eyes open - Normal state
```

### Video Feed Display
- Live webcam feed with green eye contours
- EAR value displayed in real-time
- Frame counter showing closed duration
- "DROWSINESS ALERT!" warning when triggered

## Safety Notes

⚠️ **Important Warnings:**
- This is a **prototype/educational project**, not certified safety equipment
- Do NOT rely on this as sole safety measure for driving
- MQ-6 sensors require calibration and may not be legally accurate
- Always follow traffic laws and drive responsibly
- Never drive under the influence of alcohol
- Consult professional safety equipment for real-world applications

## Enhancements & Future Improvements

- Add LCD display for visual feedback
- Implement data logging to SD card
- Add WiFi module for remote monitoring
- Use camera-based eye detection with OpenCV
- Add GPS module for location tracking
- Implement multiple sensitivity levels
- Add smartphone app integration via Bluetooth

## Project Structure

```
AlcoholDrowsinessDetector/
├── AlcoholDrowsinessDetector.ino    # Arduino sketch (alcohol + alert control)
├── eye_detection.py                  # Python script (MediaPipe eye detection)
├── requirements.txt                  # Python dependencies
└── README.md                         # This file
```

## Code Structure

### Arduino (`AlcoholDrowsinessDetector.ino`)
- `setup()`: Initializes pins, serial communication, and sensor warm-up
- `loop()`: Main monitoring loop (checks serial and MQ-6 sensor)
- `activateAlert()`: Turns on buzzer and LED
- `deactivateAlert()`: Turns off buzzer and LED

### Python (`eye_detection.py`)
- `eye_aspect_ratio()`: Calculates EAR from MediaPipe eye landmarks
- `get_eye_landmarks()`: Extracts eye coordinates from MediaPipe Face Mesh
- `find_arduino_port()`: Auto-detects Arduino COM port
- `main()`: Main loop for camera capture, MediaPipe face detection, and Arduino communication

## License

This project is open-source and available for educational purposes.

## Author

Created for Arduino-based driver safety monitoring system.

---

**Last Updated:** October 2025
