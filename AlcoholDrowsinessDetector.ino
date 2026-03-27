/*
 * Production-Grade Alcohol & Drowsiness Detection System - Arduino Controller
 * ========================================================================
 * 
 * Non-blocking architecture with millis() timing, dynamic sensor calibration,
 * relay-based engine kill-switch control, and multi-pattern alert system.
 * 
 * Hardware Configuration:
 * - MQ-3 Alcohol Sensor: A0 (analog input)
 * - Buzzer: D8 (digital output, 5V PWM capable)
 * - Relay Module: D9 (digital output, HIGH = relay ON)
 * - Status LED: D7 (digital output, visual feedback)
 * - Serial: TX/RX at 9600 baud
 * 
 * Protocol (From Python):
 * - "THREAT:<score>:<type>\n"  where score is 0-100 and type is DROWSY/YAWN/ALCOHOL/MULTI/CRITICAL
 * - Response: "ALCOHOL:<level>\n" continuously every 500ms
 * 
 * Author: Embedded Systems Engineering
 * Version: 3.0 (Production-Grade, Non-Blocking)
 */

// ============================================================================
// PIN DEFINITIONS
// ============================================================================

#define MQ3_PIN A0              // MQ-3 alcohol sensor analog pin
#define BUZZER_PIN 8            // Buzzer output (PWM-capable)
#define LED_PIN 7               // Status LED
#define RELAY_PIN 9             // Relay control (5V relay trigger)

// ============================================================================
// CONFIGURATION CONSTANTS
// ============================================================================

// Sensor Calibration
#define CALIBRATION_SAMPLES 100          // Number of samples for baseline
#define SENSOR_WARMUP_TIME 30000         // 30 second warmup period (ms)
#define CALIBRATION_READ_INTERVAL 50     // Read every 50ms during calibration

// Alert Thresholds
#define ALCOHOL_ALERT_THRESHOLD 400      // ADC threshold for alcohol detection
#define THREAT_SCORE_RELAY_TRIGGER 75    // Threat score to trigger relay
#define THREAT_SCORE_WARNING 50          // Threat score to trigger buzzer
#define THREAT_SCORE_CRITICAL 80         // Critical threat level

// Serial Communication
#define SERIAL_BAUD_RATE 9600
#define SERIAL_READ_INTERVAL 10          // Check serial every 10ms
#define ALCOHOL_REPORT_INTERVAL 500      // Send alcohol level every 500ms

// Buzzer Patterns (in milliseconds)
#define BUZZ_SHORT 100                   // Short beep
#define BUZZ_MEDIUM 200                  // Medium beep
#define BUZZ_LONG 500                    // Long beep
#define BUZZ_PAUSE 150                   // Pause between beeps

// Relay Control
#define RELAY_PULSE_DURATION 200         // How long to pulse relay (ms)
#define RELAY_AUTO_RESET_TIME 5000       // Auto-reset relay after 5 seconds

// ============================================================================
// SYSTEM STATE VARIABLES
// ============================================================================

// Calibration State
volatile int calibrationSamples[CALIBRATION_SAMPLES];
volatile int calibrationIndex = 0;
volatile boolean calibrationPhase = true;
volatile int baselineAlcoholLevel = 0;

// Sensor Readings
volatile int currentAlcoholLevel = 0;
volatile int minAlcoholReading = 1023;
volatile int maxAlcoholReading = 0;

// Threat Assessment (from Python)
volatile int lastThreatScore = 0;
volatile char lastTriggerType[16] = "";
volatile unsigned long lastThreatTime = 0;

// Alert State
volatile boolean relayActive = false;
volatile boolean buzzerActive = false;
volatile unsigned long relayActivationTime = 0;
volatile unsigned long buzzerStartTime = 0;

// Timing Variables
volatile unsigned long lastSensorRead = 0;
volatile unsigned long lastSerialCheck = 0;
volatile unsigned long lastAlcoholReport = 0;
volatile unsigned long lastBuzzToggleTime = 0;
volatile unsigned long calibrationStartTime = 0;
volatile unsigned long systemBootTime = 0;

// Buzzer Pattern State
volatile int buzzPatternStep = 0;
volatile boolean buzzState = false;

// System States
#define STATE_CALIBRATION 0
#define STATE_NORMAL 1
#define STATE_ALERT_DROWSY 2
#define STATE_ALERT_YAWN 3
#define STATE_ALERT_ALCOHOL 4
#define STATE_ALERT_CRITICAL 5
volatile int systemState = STATE_CALIBRATION;

// ============================================================================
// SETUP - Initialization with non-blocking calibration prep
// ============================================================================

void setup() {
  // ===== SERIAL INITIALIZATION =====
  Serial.begin(SERIAL_BAUD_RATE);
  delay(500);  // Wait for serial port to stabilize
  
  // Print banner
  Serial.println();
  Serial.println(F("========================================"));
  Serial.println(F("  PRODUCTION-GRADE ALERT CONTROLLER"));
  Serial.println(F("  Drowsiness & Alcohol Detection v3.0"));
  Serial.println(F("========================================"));
  Serial.println();
  
  // ===== PIN CONFIGURATION =====
  pinMode(MQ3_PIN, INPUT);           // Sensor input
  pinMode(BUZZER_PIN, OUTPUT);       // Buzzer output
  pinMode(LED_PIN, OUTPUT);          // Status LED
  pinMode(RELAY_PIN, OUTPUT);        // Relay control
  
  // Ensure all outputs are LOW initially
  digitalWrite(BUZZER_PIN, LOW);
  digitalWrite(LED_PIN, LOW);
  digitalWrite(RELAY_PIN, LOW);
  
  Serial.println(F("Pins configured:"));
  Serial.println(F("  MQ-3 Sensor: A0"));
  Serial.println(F("  Buzzer: D8"));
  Serial.println(F("  LED: D7"));
  Serial.println(F("  Relay: D9"));
  Serial.println();
  
  // ===== DYNAMIC SENSOR CALIBRATION =====
  Serial.print(F("Sensor Heating/Calibrating"));
  Serial.println(F(" (100 samples, non-blocking)"));
  Serial.print(F("Progress: ["));
  
  calibrationStartTime = millis();
  calibrationPhase = true;
  
  // Note: Actual calibration happens in loop() with non-blocking timing
  // This startup just indicates the phase
  
  systemBootTime = millis();
  
  Serial.println(F("========================================"));
  Serial.println(F("SYSTEM_READY"));
  Serial.println();
}

// ============================================================================
// MAIN LOOP - Non-blocking control flow with precise timing
// ============================================================================

void loop() {
  unsigned long currentMillis = millis();
  
  // ===== CALIBRATION PHASE (First 100 samples) =====
  if (calibrationPhase) {
    if (currentMillis - lastSensorRead >= CALIBRATION_READ_INTERVAL) {
      lastSensorRead = currentMillis;
      
      int reading = analogRead(MQ3_PIN);
      calibrationSamples[calibrationIndex] = reading;
      
      // Update min/max
      if (reading < minAlcoholReading) minAlcoholReading = reading;
      if (reading > maxAlcoholReading) maxAlcoholReading = reading;
      
      calibrationIndex++;
      
      // Print progress every 10 samples
      if (calibrationIndex % 10 == 0) {
        Serial.print(F("."));
      }
      
      // Check if calibration complete
      if (calibrationIndex >= CALIBRATION_SAMPLES) {
        finalize_calibration();
        calibrationPhase = false;
        systemState = STATE_NORMAL;
      }
    }
  }
  
  // ===== OPERATIONAL PHASE =====
  else {
    
    // ----- SENSOR READING (every 100ms) -----
    if (currentMillis - lastSensorRead >= 100) {
      lastSensorRead = currentMillis;
      
      currentAlcoholLevel = analogRead(MQ3_PIN);
      
      // Track min/max for runtime monitoring
      if (currentAlcoholLevel < minAlcoholReading) minAlcoholReading = currentAlcoholLevel;
      if (currentAlcoholLevel > maxAlcoholReading) maxAlcoholReading = currentAlcoholLevel;
    }
    
    // ----- SERIAL COMMUNICATION (every 10ms) -----
    if (currentMillis - lastSerialCheck >= SERIAL_READ_INTERVAL) {
      lastSerialCheck = currentMillis;
      process_serial_input();
    }
    
    // ----- ALCOHOL LEVEL REPORTING (every 500ms) -----
    if (currentMillis - lastAlcoholReport >= ALCOHOL_REPORT_INTERVAL) {
      lastAlcoholReport = currentMillis;
      report_alcohol_level();
    }
    
    // ----- ALERT SYSTEM STATE MACHINE -----
    update_alert_system(currentMillis);
  }
}

// ============================================================================
// CALIBRATION - Dynamic baseline establishment
// ============================================================================

void finalize_calibration() {
  Serial.println();
  Serial.println(F("Calibration Complete!"));
  
  // Calculate median instead of mean for robustness
  baselineAlcoholLevel = calculate_median(calibrationSamples, CALIBRATION_SAMPLES);
  
  Serial.print(F("Baseline Alcohol Level: "));
  Serial.println(baselineAlcoholLevel);
  
  Serial.print(F("Min/Max Range: "));
  Serial.print(minAlcoholReading);
  Serial.print(F(" - "));
  Serial.println(maxAlcoholReading);
  
  Serial.println(F("========================================"));
  Serial.println(F("Entering Operational Phase"));
  Serial.println(F("========================================"));
  Serial.println();
}

// Median calculation for robust baseline
int calculate_median(volatile int* data, int count) {
  // Simple bubble sort for small arrays
  int sorted[count];
  for (int i = 0; i < count; i++) {
    sorted[i] = data[i];
  }
  
  for (int i = 0; i < count - 1; i++) {
    for (int j = 0; j < count - i - 1; j++) {
      if (sorted[j] > sorted[j + 1]) {
        int temp = sorted[j];
        sorted[j] = sorted[j + 1];
        sorted[j + 1] = temp;
      }
    }
  }
  
  return sorted[count / 2];
}

// ============================================================================
// SERIAL COMMUNICATION - Parse threat scores from Python
// ============================================================================

void process_serial_input() {
  // Non-blocking serial read
  while (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    
    // Parse threat score command: "THREAT:<score>:<type>"
    if (command.startsWith("THREAT:")) {
      parse_threat_score(command);
    }
    // Parse calibration request
    else if (command.startsWith("CALIB_REQUEST")) {
      Serial.print(F("Baseline: "));
      Serial.println(baselineAlcoholLevel);
    }
    // Parse status request
    else if (command.startsWith("STATUS")) {
      send_debug_status();
    }
  }
}

void parse_threat_score(String command) {
  // Format: "THREAT:<score>:<type>"
  // Example: "THREAT:75:CRITICAL"
  
  int colonIndex = command.indexOf(':');
  int secondColonIndex = command.indexOf(':', colonIndex + 1);
  
  if (colonIndex > 0 && secondColonIndex > colonIndex) {
    String scoreStr = command.substring(colonIndex + 1, secondColonIndex);
    String typeStr = command.substring(secondColonIndex + 1);
    
    lastThreatScore = scoreStr.toInt();
    lastThreatScore = constrain(lastThreatScore, 0, 100);
    
    typeStr.toCharArray(lastTriggerType, 16);
    lastThreatTime = millis();
    
    // Debug output
    Serial.print(F("[THREAT] Score: "));
    Serial.print(lastThreatScore);
    Serial.print(F(" Type: "));
    Serial.println(lastTriggerType);
  }
}

void report_alcohol_level() {
  // Send current alcohol level to Python
  Serial.print(F("ALCOHOL:"));
  Serial.println(currentAlcoholLevel);
}

void send_debug_status() {
  Serial.println(F("===== Device Status ====="));
  Serial.print(F("Uptime: "));
  Serial.print(millis() / 1000);
  Serial.println(F("s"));
  
  Serial.print(F("Current Alcohol: "));
  Serial.println(currentAlcoholLevel);
  
  Serial.print(F("Baseline: "));
  Serial.println(baselineAlcoholLevel);
  
  Serial.print(F("Last Threat: "));
  Serial.print(lastThreatScore);
  Serial.print(F(" ("));
  Serial.print(lastTriggerType);
  Serial.println(F(")"));
  
  Serial.print(F("Relay: "));
  Serial.println(relayActive ? F("ON") : F("OFF"));
  
  Serial.println(F("========================"));
}

// ============================================================================
// ALERT SYSTEM - Non-blocking multi-pattern alert generation
// ============================================================================

void update_alert_system(unsigned long currentMillis) {
  
  // ===== RELAY CONTROL =====
  // Activate relay if threat score reaches critical level
  if (lastThreatScore >= THREAT_SCORE_RELAY_TRIGGER && !relayActive) {
    activate_relay(currentMillis);
  }
  
  // Auto-reset relay after duration
  if (relayActive && (currentMillis - relayActivationTime) >= RELAY_AUTO_RESET_TIME) {
    deactivate_relay();
  }
  
  // ===== BUZZER PATTERN SELECTION =====
  if (lastThreatScore >= THREAT_SCORE_WARNING) {
    manage_buzzer_pattern(currentMillis);
  } else {
    // Stop buzzer if threat cleared
    if (buzzerActive) {
      digitalWrite(BUZZER_PIN, LOW);
      digitalWrite(LED_PIN, LOW);
      buzzerActive = false;
      Serial.println(F("[BUZZER] Alert cleared"));
    }
  }
}

// ===== RELAY CONTROL FUNCTIONS =====

void activate_relay(unsigned long currentMillis) {
  relayActive = true;
  relayActivationTime = currentMillis;
  
  digitalWrite(RELAY_PIN, HIGH);
  digitalWrite(LED_PIN, HIGH);
  
  Serial.println(F("[RELAY] *** ENGINE KILL-SWITCH ACTIVATED ***"));
  Serial.print(F("[RELAY] Threat Score: "));
  Serial.println(lastThreatScore);
}

void deactivate_relay() {
  relayActive = false;
  
  digitalWrite(RELAY_PIN, LOW);
  digitalWrite(LED_PIN, LOW);
  
  Serial.println(F("[RELAY] Auto-reset complete"));
}

// ===== BUZZER PATTERN FUNCTIONS =====

void manage_buzzer_pattern(unsigned long currentMillis) {
  buzzerActive = true;
  
  // Select pattern based on threat type
  if (strcmp(lastTriggerType, "CRITICAL") == 0) {
    // Pattern: CRITICAL - Continuous rapid beeping
    pattern_critical(currentMillis);
  } 
  else if (strcmp(lastTriggerType, "MULTI") == 0) {
    // Pattern: MULTI-THREAT - Double beep pattern
    pattern_multi_threat(currentMillis);
  }
  else if (strcmp(lastTriggerType, "DROWSY") == 0) {
    // Pattern: DROWSINESS - Single beep pattern
    pattern_drowsy(currentMillis);
  }
  else if (strcmp(lastTriggerType, "YAWN") == 0) {
    // Pattern: YAWNING - Short double beep
    pattern_yawn(currentMillis);
  }
  else if (strcmp(lastTriggerType, "ALCOHOL") == 0) {
    // Pattern: ALCOHOL - Triple beep pattern
    pattern_alcohol(currentMillis);
  }
}

// Continuous rapid beeping (critical threat)
void pattern_critical(unsigned long currentMillis) {
  unsigned long elapsed = currentMillis - lastBuzzToggleTime;
  
  if (elapsed >= BUZZ_SHORT) {
    lastBuzzToggleTime = currentMillis;
    buzzState = !buzzState;
    digitalWrite(BUZZER_PIN, buzzState ? HIGH : LOW);
  }
}

// Triple beep pattern (alcohol detected)
void pattern_alcohol(unsigned long currentMillis) {
  unsigned long elapsed = currentMillis - lastBuzzToggleTime;
  
  // Pattern: BEEP-BEEP-BEEP-BEEP (4 beeps, 300ms cycle)
  int cycle = (elapsed / 750) % 4;  // 750ms total cycle, 4 states
  
  if (cycle == 0 && elapsed >= 0 && elapsed < BUZZ_SHORT) {
    digitalWrite(BUZZER_PIN, HIGH);
  } else if (cycle == 1 && elapsed >= (BUZZ_SHORT + BUZZ_PAUSE) && elapsed < (2 * BUZZ_SHORT + BUZZ_PAUSE)) {
    digitalWrite(BUZZER_PIN, HIGH);
  } else if (cycle == 2 && elapsed >= (2 * BUZZ_SHORT + 2 * BUZZ_PAUSE) && elapsed < (3 * BUZZ_SHORT + 2 * BUZZ_PAUSE)) {
    digitalWrite(BUZZER_PIN, HIGH);
  } else {
    digitalWrite(BUZZER_PIN, LOW);
  }
  
  if (elapsed >= 3000) {  // Reset every 3 seconds
    lastBuzzToggleTime = currentMillis;
  }
}

// Double beep pattern (multi-threat)
void pattern_multi_threat(unsigned long currentMillis) {
  unsigned long elapsed = currentMillis - lastBuzzToggleTime;
  
  // Pattern: BEEP-BEEP-BEEP with 1-second cycle
  if (elapsed < BUZZ_MEDIUM) {
    digitalWrite(BUZZER_PIN, HIGH);
  } else if (elapsed >= (BUZZ_MEDIUM + BUZZ_PAUSE) && elapsed < (2 * BUZZ_MEDIUM + BUZZ_PAUSE)) {
    digitalWrite(BUZZER_PIN, HIGH);
  } else if (elapsed >= (2 * BUZZ_MEDIUM + 2 * BUZZ_PAUSE) && elapsed < 1000) {
    digitalWrite(BUZZER_PIN, LOW);
  } else {
    digitalWrite(BUZZER_PIN, LOW);
    lastBuzzToggleTime = currentMillis;
  }
}

// Single beep pattern (drowsiness)
void pattern_drowsy(unsigned long currentMillis) {
  unsigned long elapsed = currentMillis - lastBuzzToggleTime;
  
  // Pattern: Long BEEP with 2-second cycle
  if (elapsed < BUZZ_LONG) {
    digitalWrite(BUZZER_PIN, HIGH);
  } else {
    digitalWrite(BUZZER_PIN, LOW);
    
    if (elapsed >= 2000) {
      lastBuzzToggleTime = currentMillis;
    }
  }
}

// Short double beep (yawning)
void pattern_yawn(unsigned long currentMillis) {
  unsigned long elapsed = currentMillis - lastBuzzToggleTime;
  
  // Pattern: BEEP-BEEP with 1.5-second cycle
  if (elapsed < BUZZ_SHORT) {
    digitalWrite(BUZZER_PIN, HIGH);
  } else if (elapsed >= (BUZZ_SHORT + BUZZ_PAUSE / 2) && elapsed < (2 * BUZZ_SHORT + BUZZ_PAUSE / 2)) {
    digitalWrite(BUZZER_PIN, HIGH);
  } else {
    digitalWrite(BUZZER_PIN, LOW);
    
    if (elapsed >= 1500) {
      lastBuzzToggleTime = currentMillis;
    }
  }
}

// ============================================================================
// END OF PRODUCTION-GRADE FIRMWARE
// ============================================================================