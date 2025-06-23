#!/usr/bin/env python3
"""
Setup sample data for Fire Response and Monitoring System
This script creates sample sensors and emergency contacts for demonstration
"""

from app import app, db
from models import Sensor, EmergencyContact, SensorType
from datetime import datetime

def setup_sample_data():
    """Create sample sensors and emergency contacts"""
    
    with app.app_context():
        print("Setting up sample data for Fire Response and Monitoring System...")
        
        # Clear existing data
        Sensor.query.delete()
        EmergencyContact.query.delete()
        
        # Create sample sensors
        sensors = [
            {
                'name': 'Kitchen Smoke Detector',
                'sensor_type': SensorType.SMOKE,
                'location': 'Main Building - Kitchen Area',
                'latitude': 40.7128,
                'longitude': -74.0060,
                'threshold_value': 30.0,
                'arduino_port': '/dev/ttyUSB0',
                'last_reading': 15.2,
                'last_update': datetime.utcnow()
            },
            {
                'name': 'Warehouse Temperature Monitor',
                'sensor_type': SensorType.TEMPERATURE,
                'location': 'Warehouse District - Building A',
                'latitude': 40.7589,
                'longitude': -73.9851,
                'threshold_value': 65.0,
                'arduino_port': '/dev/ttyUSB1',
                'last_reading': 22.5,
                'last_update': datetime.utcnow()
            },
            {
                'name': 'Parking Garage Flame Detector',
                'sensor_type': SensorType.FLAME,
                'location': 'Underground Parking - Level B2',
                'latitude': 40.7614,
                'longitude': -73.9776,
                'threshold_value': 40.0,
                'arduino_port': '/dev/ttyACM0',
                'last_reading': 8.1,
                'last_update': datetime.utcnow()
            },
            {
                'name': 'Server Room Multi-Sensor',
                'sensor_type': SensorType.COMBINED,
                'location': 'IT Building - Server Room Floor 3',
                'latitude': 40.7505,
                'longitude': -73.9934,
                'threshold_value': 50.0,
                'arduino_port': '/dev/ttyUSB2',
                'last_reading': 18.7,
                'last_update': datetime.utcnow()
            },
            {
                'name': 'Workshop Fire Monitor',
                'sensor_type': SensorType.COMBINED,
                'location': 'Industrial Workshop - Bay 5',
                'latitude': 40.7282,
                'longitude': -74.0776,
                'threshold_value': 45.0,
                'arduino_port': '/dev/ttyUSB3',
                'last_reading': 12.3,
                'last_update': datetime.utcnow()
            }
        ]
        
        # Add sensors to database
        for sensor_data in sensors:
            sensor = Sensor(**sensor_data)
            db.session.add(sensor)
            print(f"✓ Added sensor: {sensor.name}")
        
        # Create sample emergency contacts
        contacts = [
            {
                'name': 'Fire Chief Rodriguez',
                'phone': '+1555123456',
                'email': 'chief.rodriguez@cityfire.gov',
                'role': 'fire_chief',
                'is_active': True
            },
            {
                'name': 'Emergency Dispatcher',
                'phone': '+1555987654',
                'email': 'dispatch@emergency911.gov',
                'role': 'dispatcher',
                'is_active': True
            },
            {
                'name': 'Building Security Manager',
                'phone': '+1555456789',
                'email': 'security@building.com',
                'role': 'security',
                'is_active': True
            },
            {
                'name': 'System Administrator',
                'phone': '+1555111222',
                'email': 'admin@firesystem.com',
                'role': 'admin',
                'is_active': True
            }
        ]
        
        # Add contacts to database
        for contact_data in contacts:
            contact = EmergencyContact(**contact_data)
            db.session.add(contact)
            print(f"✓ Added emergency contact: {contact.name}")
        
        # Commit all changes
        db.session.commit()
        
        print(f"\n🔥 Sample data setup complete!")
        print(f"   - Created {len(sensors)} sensors with Arduino connections")
        print(f"   - Created {len(contacts)} emergency contacts")
        print(f"   - All sensors are configured with different thresholds")
        print(f"   - Ready for Arduino hardware integration")
        
        return True

if __name__ == "__main__":
    setup_sample_data()