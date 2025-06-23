try:
    import serial
except ImportError:
    # Mock serial module for environments without hardware
    class MockSerial:
        def __init__(self, *args, **kwargs):
            pass
        def readline(self):
            return b""
        def close(self):
            pass
        @property
        def in_waiting(self):
            return 0
    
    class MockSerialModule:
        Serial = MockSerial
        class SerialException(Exception):
            pass
    
    serial = MockSerialModule()
import json
import time
import logging
from threading import Thread
from datetime import datetime
from app import app, db
from models import Sensor, SensorReading, Alert, AlertType, AlertStatus
from notifier import send_alert_notifications

logger = logging.getLogger(__name__)

class ArduinoSensorReader:
    def __init__(self):
        self.active_connections = {}
        self.running = False
        
    def start_monitoring(self):
        """Start monitoring all active sensors"""
        self.running = True
        with app.app_context():
            sensors = Sensor.query.filter_by(is_active=True).all()
            
            for sensor in sensors:
                if sensor.arduino_port:
                    thread = Thread(target=self._monitor_sensor, args=(sensor,))
                    thread.daemon = True
                    thread.start()
                    logger.info(f"Started monitoring sensor {sensor.name} on port {sensor.arduino_port}")
    
    def stop_monitoring(self):
        """Stop all sensor monitoring"""
        self.running = False
        for port, connection in self.active_connections.items():
            try:
                connection.close()
                logger.info(f"Closed connection to {port}")
            except Exception as e:
                logger.error(f"Error closing connection to {port}: {e}")
        self.active_connections.clear()
    
    def _monitor_sensor(self, sensor):
        """Monitor a single sensor"""
        try:
            # Initialize serial connection
            ser = serial.Serial(
                port=sensor.arduino_port,
                baudrate=9600,
                timeout=1
            )
            self.active_connections[sensor.arduino_port] = ser
            
            logger.info(f"Connected to sensor {sensor.name} on {sensor.arduino_port}")
            
            while self.running:
                try:
                    if ser.in_waiting > 0:
                        line = ser.readline().decode('utf-8').strip()
                        
                        if line:
                            self._process_sensor_data(sensor, line)
                    
                    time.sleep(0.1)  # Small delay to prevent CPU overload
                    
                except serial.SerialException as e:
                    logger.error(f"Serial error for sensor {sensor.name}: {e}")
                    break
                except Exception as e:
                    logger.error(f"Error reading from sensor {sensor.name}: {e}")
                    time.sleep(1)  # Wait before retrying
                    
        except serial.SerialException as e:
            logger.error(f"Could not connect to sensor {sensor.name} on {sensor.arduino_port}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error monitoring sensor {sensor.name}: {e}")
        finally:
            if sensor.arduino_port in self.active_connections:
                try:
                    self.active_connections[sensor.arduino_port].close()
                    del self.active_connections[sensor.arduino_port]
                except:
                    pass
    
    def _process_sensor_data(self, sensor, data):
        """Process incoming sensor data"""
        try:
            with app.app_context():
                # Try to parse JSON data first
                try:
                    sensor_data = json.loads(data)
                    value = float(sensor_data.get('value', 0))
                    sensor_type = sensor_data.get('type', 'temperature')
                except (json.JSONDecodeError, ValueError):
                    # If not JSON, try to parse as plain number
                    try:
                        value = float(data)
                    except ValueError:
                        logger.warning(f"Could not parse sensor data: {data}")
                        return
                
                # Update sensor last reading
                sensor.last_reading = value
                sensor.last_update = datetime.utcnow()
                
                # Store reading in database
                reading = SensorReading(
                    sensor_id=sensor.id,
                    value=value,
                    timestamp=datetime.utcnow()
                )
                db.session.add(reading)
                
                # Check if value exceeds threshold
                if value > sensor.threshold_value:
                    self._create_fire_alert(sensor, value)
                
                db.session.commit()
                logger.debug(f"Processed reading for {sensor.name}: {value}")
                
        except Exception as e:
            logger.error(f"Error processing sensor data for {sensor.name}: {e}")
            db.session.rollback()
    
    def _create_fire_alert(self, sensor, reading_value):
        """Create a fire alert when sensor threshold is exceeded"""
        try:
            # Check if there's already an active alert for this sensor
            existing_alert = Alert.query.filter_by(
                sensor_id=sensor.id,
                status=AlertStatus.ACTIVE
            ).first()
            
            if existing_alert:
                logger.debug(f"Alert already exists for sensor {sensor.name}")
                return
            
            # Determine severity based on how much the threshold is exceeded
            threshold_ratio = reading_value / sensor.threshold_value
            if threshold_ratio >= 3:
                severity = 'critical'
            elif threshold_ratio >= 2:
                severity = 'high'
            elif threshold_ratio >= 1.5:
                severity = 'medium'
            else:
                severity = 'low'
            
            # Create new alert
            alert = Alert(
                title=f"Fire Detected - {sensor.name}",
                description=f"Sensor {sensor.name} detected reading of {reading_value:.2f} "
                           f"(threshold: {sensor.threshold_value:.2f})",
                alert_type=AlertType.SENSOR_DETECTION,
                status=AlertStatus.ACTIVE,
                severity=severity,
                latitude=sensor.latitude or 0.0,
                longitude=sensor.longitude or 0.0,
                address=sensor.location,
                sensor_id=sensor.id,
                sensor_reading=reading_value
            )
            
            db.session.add(alert)
            db.session.commit()
            
            logger.warning(f"FIRE ALERT CREATED: {alert.title} - Severity: {severity}")
            
            # Send notifications asynchronously
            notification_thread = Thread(target=send_alert_notifications, args=(alert.id,))
            notification_thread.daemon = True
            notification_thread.start()
            
        except Exception as e:
            logger.error(f"Error creating fire alert: {e}")
            db.session.rollback()

# Global sensor reader instance
sensor_reader = ArduinoSensorReader()

def start_sensor_monitoring():
    """Start the sensor monitoring system"""
    sensor_reader.start_monitoring()

def stop_sensor_monitoring():
    """Stop the sensor monitoring system"""
    sensor_reader.stop_monitoring()

def test_sensor_reading(sensor_id, test_value):
    """Test function to simulate sensor reading"""
    with app.app_context():
        sensor = Sensor.query.get(sensor_id)
        if sensor:
            sensor_reader._process_sensor_data(sensor, str(test_value))
            return True
    return False
