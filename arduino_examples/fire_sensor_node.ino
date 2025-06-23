/*
  Fire Detection Sensor Node for Arduino
  Compatible with Fire Response and Monitoring System
  
  This code reads from multiple fire detection sensors and sends
  data to the Python monitoring system via serial communication.
  
  Hardware Requirements:
  - Arduino Uno/Nano/ESP32
  - DHT22 temperature/humidity sensor
  - MQ-2 smoke/gas sensor  
  - Flame sensor (IR)
  - LED indicators
  - Buzzer for local alerts
  
  Wiring:
  - DHT22: Data pin to digital pin 2
  - MQ-2: Analog output to A0
  - Flame sensor: Digital output to pin 3
  - Green LED: pin 8 (normal operation)
  - Red LED: pin 9 (alert condition)
  - Buzzer: pin 10
*/

#include <DHT.h>
#include <ArduinoJson.h>

// Pin definitions
#define DHT_PIN 2
#define DHT_TYPE DHT22
#define SMOKE_PIN A0
#define FLAME_PIN 3
#define GREEN_LED 8
#define RED_LED 9
#define BUZZER 10

// Sensor objects
DHT dht(DHT_PIN, DHT_TYPE);

// Configuration
const int SENSOR_ID = 1;  // Unique identifier for this sensor node
const String SENSOR_NAME = "Fire_Sensor_Node_01";
const String LOCATION = "Building_A_Kitchen";

// Thresholds (configurable via serial commands)
float temperatureThreshold = 50.0;  // Celsius
int smokeThreshold = 300;            // Analog reading (0-1023)
bool flameThreshold = true;          // Digital sensor

// Timing
unsigned long lastReading = 0;
const unsigned long READING_INTERVAL = 5000;  // 5 seconds
unsigned long lastHeartbeat = 0;
const unsigned long HEARTBEAT_INTERVAL = 30000;  // 30 seconds

// State tracking
bool alertActive = false;
bool systemOnline = true;

void setup() {
  Serial.begin(9600);
  
  // Initialize sensors
  dht.begin();
  
  // Initialize pins
  pinMode(FLAME_PIN, INPUT);
  pinMode(GREEN_LED, OUTPUT);
  pinMode(RED_LED, OUTPUT);
  pinMode(BUZZER, OUTPUT);
  
  // Initial state
  digitalWrite(GREEN_LED, HIGH);
  digitalWrite(RED_LED, LOW);
  
  // Startup sequence
  for(int i = 0; i < 3; i++) {
    digitalWrite(RED_LED, HIGH);
    delay(200);
    digitalWrite(RED_LED, LOW);
    delay(200);
  }
  
  Serial.println("{\"status\":\"SENSOR_ONLINE\",\"sensor_id\":" + String(SENSOR_ID) + ",\"name\":\"" + SENSOR_NAME + "\"}");
}

void loop() {
  // Check for serial commands
  if (Serial.available()) {
    processSerialCommand();
  }
  
  // Take sensor readings
  if (millis() - lastReading >= READING_INTERVAL) {
    takeSensorReadings();
    lastReading = millis();
  }
  
  // Send heartbeat
  if (millis() - lastHeartbeat >= HEARTBEAT_INTERVAL) {
    sendHeartbeat();
    lastHeartbeat = millis();
  }
  
  // Update LED status
  updateStatusLEDs();
  
  delay(100);
}

void takeSensorReadings() {
  // Read temperature and humidity
  float temperature = dht.readTemperature();
  float humidity = dht.readHumidity();
  
  // Read smoke sensor (analog)
  int smokeLevel = analogRead(SMOKE_PIN);
  
  // Read flame sensor (digital)
  bool flameDetected = !digitalRead(FLAME_PIN);  // Inverted logic
  
  // Check for sensor errors
  if (isnan(temperature) || isnan(humidity)) {
    Serial.println("{\"error\":\"DHT_SENSOR_ERROR\",\"sensor_id\":" + String(SENSOR_ID) + "}");
    return;
  }
  
  // Create JSON data packet
  StaticJsonDocument<300> doc;
  doc["sensor_id"] = SENSOR_ID;
  doc["name"] = SENSOR_NAME;
  doc["location"] = LOCATION;
  doc["timestamp"] = millis();
  
  // Sensor readings
  doc["temperature"] = round(temperature * 100) / 100.0;  // 2 decimal places
  doc["humidity"] = round(humidity * 100) / 100.0;
  doc["smoke_level"] = smokeLevel;
  doc["flame_detected"] = flameDetected;
  
  // Calculate fire risk score (0-100)
  int fireRisk = calculateFireRisk(temperature, smokeLevel, flameDetected);
  doc["fire_risk"] = fireRisk;
  
  // Alert conditions
  bool temperatureAlert = temperature > temperatureThreshold;
  bool smokeAlert = smokeLevel > smokeThreshold;
  bool flameAlert = flameDetected;
  
  bool currentAlertState = temperatureAlert || smokeAlert || flameAlert;
  
  doc["alerts"]["temperature"] = temperatureAlert;
  doc["alerts"]["smoke"] = smokeAlert;
  doc["alerts"]["flame"] = flameAlert;
  doc["alerts"]["active"] = currentAlertState;
  
  // Send data to monitoring system
  String output;
  serializeJson(doc, output);
  Serial.println(output);
  
  // Handle alert state changes
  if (currentAlertState && !alertActive) {
    // New alert triggered
    triggerLocalAlert();
    alertActive = true;
  } else if (!currentAlertState && alertActive) {
    // Alert cleared
    clearLocalAlert();
    alertActive = false;
  }
}

int calculateFireRisk(float temp, int smoke, bool flame) {
  int risk = 0;
  
  // Temperature contribution (0-40 points)
  if (temp > 25) risk += map(constrain(temp, 25, 100), 25, 100, 0, 40);
  
  // Smoke contribution (0-40 points)  
  if (smoke > 100) risk += map(constrain(smoke, 100, 1000), 100, 1000, 0, 40);
  
  // Flame detection (0-20 points)
  if (flame) risk += 20;
  
  return constrain(risk, 0, 100);
}

void triggerLocalAlert() {
  // Sound buzzer pattern
  for(int i = 0; i < 5; i++) {
    digitalWrite(BUZZER, HIGH);
    delay(100);
    digitalWrite(BUZZER, LOW);
    delay(100);
  }
  
  Serial.println("{\"local_alert\":\"TRIGGERED\",\"sensor_id\":" + String(SENSOR_ID) + "}");
}

void clearLocalAlert() {
  digitalWrite(BUZZER, LOW);
  Serial.println("{\"local_alert\":\"CLEARED\",\"sensor_id\":" + String(SENSOR_ID) + "}");
}

void updateStatusLEDs() {
  if (alertActive) {
    // Blink red LED for alert
    digitalWrite(RED_LED, (millis() / 500) % 2);
    digitalWrite(GREEN_LED, LOW);
  } else {
    // Solid green for normal operation
    digitalWrite(GREEN_LED, HIGH);
    digitalWrite(RED_LED, LOW);
  }
}

void sendHeartbeat() {
  StaticJsonDocument<200> doc;
  doc["heartbeat"] = true;
  doc["sensor_id"] = SENSOR_ID;
  doc["uptime"] = millis();
  doc["free_memory"] = getFreeMemory();
  doc["alert_active"] = alertActive;
  
  String output;
  serializeJson(doc, output);
  Serial.println(output);
}

void processSerialCommand() {
  String command = Serial.readStringUntil('\n');
  command.trim();
  
  if (command.startsWith("SET_TEMP_THRESHOLD:")) {
    temperatureThreshold = command.substring(19).toFloat();
    Serial.println("{\"config_updated\":\"temperature_threshold\",\"value\":" + String(temperatureThreshold) + "}");
  }
  else if (command.startsWith("SET_SMOKE_THRESHOLD:")) {
    smokeThreshold = command.substring(20).toInt();
    Serial.println("{\"config_updated\":\"smoke_threshold\",\"value\":" + String(smokeThreshold) + "}");
  }
  else if (command == "GET_STATUS") {
    StaticJsonDocument<300> doc;
    doc["sensor_id"] = SENSOR_ID;
    doc["name"] = SENSOR_NAME;
    doc["location"] = LOCATION;
    doc["uptime"] = millis();
    doc["alert_active"] = alertActive;
    doc["thresholds"]["temperature"] = temperatureThreshold;
    doc["thresholds"]["smoke"] = smokeThreshold;
    
    String output;
    serializeJson(doc, output);
    Serial.println(output);
  }
  else if (command == "TEST_ALERT") {
    triggerLocalAlert();
    Serial.println("{\"test_alert\":\"executed\"}");
  }
  else if (command == "RESET") {
    Serial.println("{\"status\":\"REBOOTING\"}");
    delay(1000);
    // Software reset (platform dependent)
    asm volatile ("  jmp 0");
  }
  else {
    Serial.println("{\"error\":\"UNKNOWN_COMMAND\",\"received\":\"" + command + "\"}");
  }
}

int getFreeMemory() {
  // Simple memory check for Arduino Uno
  extern int __heap_start, *__brkval;
  int v;
  return (int) &v - (__brkval == 0 ? (int) &__heap_start : (int) __brkval);
}

// Optional: Emergency manual override button
void checkEmergencyButton() {
  // Connect button between pin 7 and GND with pullup
  pinMode(7, INPUT_PULLUP);
  
  if (digitalRead(7) == LOW) {
    delay(50);  // Debounce
    if (digitalRead(7) == LOW) {
      // Manual emergency trigger
      StaticJsonDocument<200> doc;
      doc["manual_trigger"] = true;
      doc["sensor_id"] = SENSOR_ID;
      doc["fire_risk"] = 100;
      
      String output;
      serializeJson(doc, output);
      Serial.println(output);
      
      triggerLocalAlert();
      
      while(digitalRead(7) == LOW) delay(100);  // Wait for release
    }
  }
}