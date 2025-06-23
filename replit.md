# Fire Response and Monitoring System

## Overview

This is a Python-based Fire Response and Monitoring System built with Flask that provides real-time fire detection, alert management, and emergency response coordination. The system integrates sensor monitoring, multi-channel notifications, GPS navigation, and a web-based dashboard for comprehensive fire emergency management.

## System Architecture

### Backend Architecture
- **Framework**: Flask with SQLAlchemy ORM for database operations
- **Database**: PostgreSQL (production) with SQLite fallback for development
- **Web Server**: Gunicorn with auto-scaling deployment configuration
- **Session Management**: Flask sessions with configurable secret keys

### Frontend Architecture
- **Templates**: Jinja2 templating with Bootstrap 5 dark theme
- **JavaScript**: Vanilla JS with Chart.js for analytics visualization
- **CSS**: Custom styling with CSS variables and responsive design
- **Icons**: Feather Icons for consistent UI elements

### Database Schema
The system uses SQLAlchemy models with the following key entities:
- **Sensor**: Tracks fire detection sensors with location data and Arduino connections
- **Alert**: Manages fire alerts with status tracking and severity levels
- **SensorReading**: Historical sensor data (referenced but not fully implemented)
- **EmergencyContact**: Contact management for notifications (referenced but not fully implemented)

## Key Components

### 1. Sensor Management (`sensor_reader.py`)
- **ArduinoSensorReader**: Manages serial connections to Arduino-based fire sensors
- **Multi-threading**: Concurrent monitoring of multiple sensors
- **Real-time Processing**: Continuous sensor data reading and threshold evaluation
- **Alert Generation**: Automatic alert creation when thresholds are exceeded

### 2. Notification System (`notifier.py`)
- **Multi-channel Alerts**: SMS (Twilio) and Email (SMTP) notifications
- **Configuration-driven**: Environment variable based service configuration  
- **Error Handling**: Graceful fallback when notification services are unavailable

### 3. GPS Navigation (`gps_navigator.py`)
- **Google Maps Integration**: Address geocoding and reverse geocoding
- **Coordinate Conversion**: Two-way conversion between addresses and GPS coordinates
- **Navigation Support**: Foundation for routing emergency responders to incidents

### 4. Web Interface (`routes.py`, templates/)
- **Dashboard**: Real-time system status and alert monitoring
- **Alert Management**: Comprehensive alert listing with filtering capabilities
- **Fire Reporting**: Community-based incident reporting interface
- **Analytics**: Historical data visualization and system performance metrics

## Data Flow

1. **Sensor Detection**: Arduino sensors continuously monitor environmental conditions
2. **Data Processing**: Python backend processes sensor readings against thresholds
3. **Alert Generation**: System creates alerts when fire conditions are detected
4. **Notification Dispatch**: Multi-channel notifications sent to emergency contacts
5. **Web Updates**: Real-time dashboard updates reflect current system status
6. **Response Coordination**: GPS navigation assists emergency responder deployment

## External Dependencies

### Core Dependencies
- **Flask Ecosystem**: flask, flask-sqlalchemy, werkzeug for web framework
- **Database**: psycopg2-binary for PostgreSQL connectivity
- **Hardware Integration**: pyserial for Arduino sensor communication
- **HTTP Client**: Included for external API communications

### Third-party Services
- **Twilio**: SMS notification service (requires API credentials)
- **Google Maps**: Geocoding and navigation services (requires API key)
- **SMTP Services**: Email notifications (configurable provider)

### Development Tools
- **Gunicorn**: Production WSGI server
- **Email Validator**: Input validation for contact management

## Deployment Strategy

### Environment Configuration
- **Nix-based**: Uses stable-24_05 channel with Python 3.11
- **Database**: PostgreSQL and OpenSSL packages pre-installed
- **Auto-scaling**: Configured for automatic horizontal scaling

### Production Deployment
- **WSGI Server**: Routes through Gunicorn with multi-worker configuration
- **Port Binding**: Configured for 0.0.0.0:5000 with external accessibility
- **Process Management**: Reusable ports and reload capabilities for development

### Development Workflow
- **Parallel Tasks**: Concurrent development server and monitoring processes
- **Hot Reload**: Automatic application restart on code changes
- **Database Migration**: Automatic table creation on application startup

## User Preferences

Preferred communication style: Simple, everyday language.

## Recent Changes

**June 23, 2025 - WhatsApp Integration Complete**
- ✅ Added WhatsApp chatbot for community fire reporting
- ✅ Implemented multi-step conversation flow for location, description, and contact info
- ✅ Created intelligent severity detection from user descriptions
- ✅ Added webhook endpoint for Twilio WhatsApp integration
- ✅ Built comprehensive management interface at /whatsapp-bot
- ✅ Demonstrated complete fire reporting workflow via WhatsApp

**June 23, 2025 - Core System Setup**
- ✅ Initial Fire Response and Monitoring System setup
- ✅ Arduino sensor integration with real-time monitoring
- ✅ SMS alerts via Twilio for emergency notifications
- ✅ Web dashboard with sensor status and alert management
- ✅ GPS navigation support for emergency responders
- ✅ Community fire reporting through web interface

## Changelog

Changelog:
- June 23, 2025. WhatsApp bot integration completed
- June 23, 2025. Initial setup with Arduino compatibility