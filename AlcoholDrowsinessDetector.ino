/*
 * Alcohol and Drowsiness Detection System - Arduino Controller
 * 
 * This system monitors:
 * 1. Eye closure duration - Detected via Python script (laptop camera)
 * 2. Alcohol level via MQ-6 sensor - Alerts if level > 400
 * 
 * Hardware Connections:
 * - MQ-6 Sensor: VCC->5V, GND->GND, A0->A0
 * - Buzzer: Positive->D8, Negative->GND
 * - LED: Positive->D7 (with 220Ω resistor), Negative->GND
 * 
 * Serial Communication Protocol:
 * - Receives 'E' from Python when drowsiness detected (eyes closed > 2 sec)
 * - Receives 'N' from Python when eyes are open/normal
 * - Receives 'S' from Python to get current status
 * 
 * Author: Alcohol & Drowsiness Detection System
 * Version: 2.0 (Optimized)
 */

// Pin Definitions
#define MQ6_PIN A0           // MQ-6 alcohol sensor analog pin
#define BUZZER_PIN 8         // Buzzer output pin
#define LED_PIN 7            // LED output pin

// Thresholds and Constants
#define ALCOHOL_THRESHOLD 400     // Alcohol level threshold
#define WARMUP_TIME 20000         // MQ-6 sensor warmup time (20 seconds)
#define SENSOR_READ_INTERVAL 100  // Read sensor every 100ms
#define BEEP_INTERVAL 500         // Beep pattern interval

// Variables
int alcoholLevel = 0;
bool drowsinessDetected = false;  // Received from Python
bool alcoholDetected = false;
bool lastAlertState = false;      // Track previous alert state
bool lastAlcoholState = false;    // Track alcohol detection state
unsigned long lastSensorRead = 0;
unsigned long lastBeepToggle = 0;
unsigned long lastValueSent = 0;  // Track when we last sent alcohol value
bool beepState = false;
int minAlcoholLevel = 1023;       // Track minimum reading
int maxAlcoholLevel = 0;          // Track maximum reading

#define VALUE_SEND_INTERVAL 500   // Send alcohol value every 500ms

void setup() {
  // Initialize serial communication
  Serial.begin(9600);
  while (!Serial && millis() < 3000) {
    ; // Wait for serial port to connect, max 3 seconds
  }
  
  // Configure pins
  pinMode(MQ6_PIN, INPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(LED_PIN, OUTPUT);
  
  // Ensure buzzer and LED are off initially
  digitalWrite(BUZZER_PIN, LOW);
  digitalWrite(LED_PIN, LOW);
  
  // Startup message
  Serial.println();
  Serial.println(F("========================================"));
  Serial.println(F("  ALCOHOL & DROWSINESS DETECTION"));
  Serial.println(F("     Arduino Controller v2.0"));
  Serial.println(F("========================================"));
  Serial.println(F("READY"));
  Serial.println();
  Serial.print(F("Warming up MQ-6 sensor..."));
  
  // Allow MQ-6 sensor to warm up with progress indicator
  unsigned long startTime = millis();
  while (millis() - startTime < WARMUP_TIME) {
    if ((millis() - startTime) % 5000 == 0) {
      Serial.print(F("."));
    }
    delay(100);
  }
  
  Serial.println();
  Serial.println(F("Sensor warm-up complete!"));
  Serial.println();
  Serial.println(F("System Configuration:"));
  Serial.print(F("  - Alcohol Threshold: "));
  Serial.println(ALCOHOL_THRESHOLD);
  Serial.print(F("  - Buzzer Pin: D"));
  Serial.println(BUZZER_PIN);
  Serial.print(F("  - LED Pin: D"));
  Serial.println(LED_PIN);
  Serial.println(F("  - MQ-6 Pin: A0"));
  Serial.println();
  Serial.println(F("Commands:"));
  Serial.println(F("  'E' = Eyes closed (drowsy)"));
  Serial.println(F("  'N' = Eyes open (normal)"));
  Serial.println(F("  'S' = Status request"));
  Serial.println(F("========================================"));
  Serial.println(F("SYSTEM_READY"));
  Serial.println();
}

void loop() {
  unsigned long currentMillis = millis();
  
  // Check for commands from Python (eye detection)
  if (Serial.available() > 0) {
    char command = Serial.read();
    
    switch (command) {
      case 'E':  // Eyes closed - Drowsiness detected
        if (!drowsinessDetected) {
          drowsinessDetected = true;
          Serial.println(F(">>> DROWSY"));
        }
        break;
        
      case 'N':  // Eyes open - Normal state
        if (drowsinessDetected) {
          drowsinessDetected = false;
          Serial.println(F(">>> NORMAL"));
        }
        break;
        
      case 'S':  // Status request
        sendStatus();
        break;
        
      default:
        // Ignore unknown commands
        break;
    }
  }
  
  // Read alcohol sensor at specified interval
  if (currentMillis - lastSensorRead >= SENSOR_READ_INTERVAL) {
    lastSensorRead = currentMillis;
    alcoholLevel = analogRead(MQ6_PIN);
    
    // Track min/max for calibration
    if (alcoholLevel < minAlcoholLevel) minAlcoholLevel = alcoholLevel;
    if (alcoholLevel > maxAlcoholLevel) maxAlcoholLevel = alcoholLevel;
    
    // Send current alcohol level to Python periodically
    if (currentMillis - lastValueSent >= VALUE_SEND_INTERVAL) {
      lastValueSent = currentMillis;
      Serial.print(F("Level = "));
      Serial.println(alcoholLevel);
    }
    
    // Check alcohol level threshold
    if (alcoholLevel > ALCOHOL_THRESHOLD) {
      if (!alcoholDetected) {
        alcoholDetected = true;
        lastAlcoholState = true;
        Serial.print(F(">>> ALCOHOL_DETECTED: Level = "));
        Serial.println(alcoholLevel);
      }
    } else {
      if (alcoholDetected) {
        alcoholDetected = false;
        lastAlcoholState = false;
        Serial.println(F(">>> ALCOHOL_NORMAL"));
      }
    }
  }
  
  // Determine if alert should be active
  bool currentAlertState = (drowsinessDetected || alcoholDetected);
  
  // Manage alert system
  if (currentAlertState) {
    // Alert mode with pulsing pattern
    if (currentMillis - lastBeepToggle >= BEEP_INTERVAL) {
      lastBeepToggle = currentMillis;
      beepState = !beepState;
      
      if (beepState) {
        digitalWrite(BUZZER_PIN, HIGH);
        digitalWrite(LED_PIN, HIGH);
      } else {
        digitalWrite(BUZZER_PIN, LOW);
        digitalWrite(LED_PIN, LOW);
      }
    }
    
    // Send alert message only when state changes
    if (!lastAlertState) {
      if (drowsinessDetected && alcoholDetected) {
        Serial.println(F("!!! ALERT:BOTH - DROWSY + ALCOHOL !!!"));
      } else if (drowsinessDetected) {
        Serial.println(F("!!! ALERT:DROWSY !!!"));
      } else if (alcoholDetected) {
        Serial.println(F("!!! ALERT:ALCOHOL !!!"));
      }
    }
  } else {
    // Normal mode - ensure buzzer and LED are off
    digitalWrite(BUZZER_PIN, LOW);
    digitalWrite(LED_PIN, LOW);
    beepState = false;
    
    // Clear alert message when returning to normal
    if (lastAlertState) {
      Serial.println(F(">>> Alert cleared - Normal operation"));
    }
  }
  
  lastAlertState = currentAlertState;
}

// Function to send current system status
void sendStatus() {
  Serial.println(F("========== SYSTEM STATUS =========="));
  Serial.print(F("Alcohol Level: "));
  Serial.print(alcoholLevel);
  Serial.print(F(" (Min: "));
  Serial.print(minAlcoholLevel);
  Serial.print(F(", Max: "));
  Serial.print(maxAlcoholLevel);
  Serial.println(F(")"));
  Serial.print(F("Threshold: "));
  Serial.println(ALCOHOL_THRESHOLD);
  Serial.print(F("Drowsiness: "));
  Serial.println(drowsinessDetected ? F("DETECTED") : F("Normal"));
  Serial.print(F("Alcohol: "));
  Serial.println(alcoholDetected ? F("DETECTED") : F("Normal"));
  Serial.print(F("Alert Status: "));
  Serial.println(lastAlertState ? F("ACTIVE") : F("Inactive"));
  Serial.print(F("Uptime: "));
  Serial.print(millis() / 1000);
  Serial.println(F(" seconds"));
  Serial.println(F("==================================="));
}

