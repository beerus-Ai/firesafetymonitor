# Arduino Integration Guide

## Fire Sensor Node Setup

The Fire Response and Monitoring System is designed to work with Arduino-based sensor nodes that detect fire conditions in real-time.

### Hardware Requirements

**Sensors:**
- DHT22: Temperature and humidity monitoring
- MQ-2: Smoke and gas detection  
- IR Flame Sensor: Direct flame detection
- Analog temperature sensors (optional backup)

**Indicators:**
- Green LED: Normal operation status
- Red LED: Alert condition indicator
- Buzzer: Local audio alerts

**Connectivity:**
- USB cable for serial communication
- Optional: ESP32/WiFi modules for wireless connectivity

### Wiring Diagram

```
Arduino Uno Connections:
┌─────────────────┐
│     Arduino     │
│                 │
│ A0  ── MQ-2     │ (Smoke sensor analog out)
│ D2  ── DHT22    │ (Temperature/humidity data)
│ D3  ── Flame    │ (IR flame sensor digital out)
│ D7  ── Button   │ (Manual emergency trigger)
│ D8  ── Green LED│ (Status indicator)
│ D9  ── Red LED  │ (Alert indicator)
│ D10 ── Buzzer   │ (Local alarm)
│                 │
│ GND ── Common   │
│ 5V  ── VCC      │
└─────────────────┘
```

### Serial Communication Protocol

The Arduino sends JSON data packets via serial at 9600 baud:

```json
{
  "sensor_id": 1,
  "name": "Fire_Sensor_Node_01",
  "location": "Building_A_Kitchen",
  "timestamp": 150000,
  "temperature": 24.50,
  "humidity": 45.20,
  "smoke_level": 150,
  "flame_detected": false,
  "fire_risk": 15,
  "alerts": {
    "temperature": false,
    "smoke": false,
    "flame": false,
    "active": false
  }
}
```

### Installation Steps

1. **Hardware Assembly:**
   - Connect sensors according to wiring diagram
   - Install LEDs and buzzer for local feedback
   - Mount in protective enclosure

2. **Software Upload:**
   - Install Arduino IDE with required libraries:
     - DHT sensor library
     - ArduinoJson library
   - Upload `fire_sensor_node.ino` to Arduino
   - Configure sensor ID and location in code

3. **System Integration:**
   - Connect Arduino to monitoring system via USB
   - Update sensor configuration in Python system:
     ```python
     sensor = Sensor(
         name="Kitchen Smoke Detector",
         arduino_port="/dev/ttyUSB0",  # Adjust port
         threshold_value=50.0
     )
     ```
   - Verify sensor appears in web dashboard

4. **Testing:**
   - Use "Test Sensor" button in web interface
   - Verify alerts trigger at configured thresholds
   - Confirm SMS/email notifications work
   - Test manual emergency button

### Commands

Send these commands via serial to configure sensors:

- `SET_TEMP_THRESHOLD:60.0` - Set temperature alert threshold
- `SET_SMOKE_THRESHOLD:400` - Set smoke level threshold  
- `GET_STATUS` - Request current sensor status
- `TEST_ALERT` - Trigger test alert condition
- `RESET` - Restart sensor node

### Troubleshooting

**Sensor Not Detected:**
- Check USB cable and port assignment
- Verify Arduino is powered and running
- Confirm baud rate is 9600

**False Alarms:**
- Adjust threshold values via web interface
- Check sensor placement and environmental factors
- Calibrate sensors in clean air conditions

**Communication Issues:**
- Restart sensor monitoring service
- Check serial port permissions
- Verify JSON format in serial output

### Multiple Sensor Deployment

For building-wide coverage:

1. Deploy sensors in key locations (kitchen, server room, garage)
2. Configure unique sensor IDs and names
3. Use USB hubs or individual ports for multiple connections
4. Consider wireless modules for remote locations
5. Set up redundant sensors for critical areas

### Maintenance

- Monthly sensor calibration checks
- Battery backup for power outages
- Regular cleaning of smoke sensors
- Firmware updates for bug fixes and new features