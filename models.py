from app import db
from datetime import datetime
from sqlalchemy import Enum
import enum

class AlertStatus(enum.Enum):
    ACTIVE = "active"
    RESOLVED = "resolved"
    FALSE_ALARM = "false_alarm"

class AlertType(enum.Enum):
    SENSOR_DETECTION = "sensor_detection"
    COMMUNITY_REPORT = "community_report"
    MANUAL_TRIGGER = "manual_trigger"

class SensorType(enum.Enum):
    TEMPERATURE = "temperature"
    SMOKE = "smoke"
    FLAME = "flame"
    COMBINED = "combined"

class Sensor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    sensor_type = db.Column(Enum(SensorType), nullable=False)
    location = db.Column(db.String(200))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    is_active = db.Column(db.Boolean, default=True)
    last_reading = db.Column(db.Float)
    last_update = db.Column(db.DateTime, default=datetime.utcnow)
    threshold_value = db.Column(db.Float, default=50.0)  # Default threshold
    arduino_port = db.Column(db.String(50))  # Serial port for Arduino connection
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship with alerts
    alerts = db.relationship('Alert', backref='sensor', lazy=True)

class Alert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    alert_type = db.Column(Enum(AlertType), nullable=False)
    status = db.Column(Enum(AlertStatus), default=AlertStatus.ACTIVE)
    severity = db.Column(db.String(20), default='medium')  # low, medium, high, critical
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    address = db.Column(db.String(300))
    sensor_id = db.Column(db.Integer, db.ForeignKey('sensor.id'), nullable=True)
    sensor_reading = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime)
    
    # SMS and Email notification tracking
    sms_sent = db.Column(db.Boolean, default=False)
    email_sent = db.Column(db.Boolean, default=False)
    
    # Community reporting fields
    reporter_name = db.Column(db.String(100))
    reporter_phone = db.Column(db.String(20))
    reporter_email = db.Column(db.String(100))

class SensorReading(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sensor_id = db.Column(db.Integer, db.ForeignKey('sensor.id'), nullable=False)
    value = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    sensor = db.relationship('Sensor', backref='readings')

class EmergencyContact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100))
    role = db.Column(db.String(50), default='responder')  # responder, admin, observer
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
