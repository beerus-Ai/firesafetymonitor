from flask import render_template, request, jsonify, redirect, url_for, flash
from datetime import datetime, timedelta
from app import app, db
from models import Sensor, Alert, SensorReading, EmergencyContact, AlertStatus, AlertType, SensorType
from sensor_reader import test_sensor_reading, sensor_reader
from notifier import send_alert_notifications, send_test_notifications
from gps_navigator import get_navigation_to_alert, geocode_address, reverse_geocode, find_fire_stations
import logging

logger = logging.getLogger(__name__)

@app.route('/')
def index():
    """Main dashboard page"""
    # Get recent alerts
    recent_alerts = Alert.query.filter_by(status=AlertStatus.ACTIVE).order_by(Alert.created_at.desc()).limit(5).all()
    
    # Get sensor status
    sensors = Sensor.query.filter_by(is_active=True).all()
    
    # Get system statistics
    total_alerts_today = Alert.query.filter(
        Alert.created_at >= datetime.utcnow().date()
    ).count()
    
    active_alerts_count = Alert.query.filter_by(status=AlertStatus.ACTIVE).count()
    
    return render_template('index.html',
                         recent_alerts=recent_alerts,
                         sensors=sensors,
                         total_alerts_today=total_alerts_today,
                         active_alerts_count=active_alerts_count)

@app.route('/dashboard')
def dashboard():
    """Detailed dashboard with charts and analytics"""
    # Get alerts for the last 30 days
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    alerts = Alert.query.filter(Alert.created_at >= thirty_days_ago).all()
    
    # Get all sensors with their latest readings
    sensors = Sensor.query.filter_by(is_active=True).all()
    
    # Get emergency contacts
    contacts = EmergencyContact.query.filter_by(is_active=True).all()
    
    return render_template('dashboard.html',
                         alerts=alerts,
                         sensors=sensors,
                         contacts=contacts)

@app.route('/alerts')
def alerts():
    """Show all alerts with filtering options"""
    status_filter = request.args.get('status', 'all')
    severity_filter = request.args.get('severity', 'all')
    
    query = Alert.query
    
    if status_filter != 'all':
        query = query.filter_by(status=AlertStatus(status_filter))
    
    if severity_filter != 'all':
        query = query.filter_by(severity=severity_filter)
    
    alerts = query.order_by(Alert.created_at.desc()).all()
    
    return render_template('alerts.html', alerts=alerts)

@app.route('/report-fire')
def report_fire():
    """Community fire reporting form"""
    return render_template('report_fire.html')

@app.route('/whatsapp-bot')
def whatsapp_bot():
    """WhatsApp bot management page"""
    return render_template('whatsapp_bot.html')

@app.route('/api/report-fire', methods=['POST'])
def api_report_fire():
    """API endpoint for community fire reports"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['latitude', 'longitude', 'description']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Get address from coordinates
        address = reverse_geocode(data['latitude'], data['longitude'])
        
        # Create alert
        alert = Alert(
            title="Community Fire Report",
            description=data['description'],
            alert_type=AlertType.COMMUNITY_REPORT,
            status=AlertStatus.ACTIVE,
            severity=data.get('severity', 'medium'),
            latitude=float(data['latitude']),
            longitude=float(data['longitude']),
            address=address,
            reporter_name=data.get('reporter_name'),
            reporter_phone=data.get('reporter_phone'),
            reporter_email=data.get('reporter_email')
        )
        
        db.session.add(alert)
        db.session.commit()
        
        # Send notifications
        from threading import Thread
        notification_thread = Thread(target=send_alert_notifications, args=(alert.id,))
        notification_thread.daemon = True
        notification_thread.start()
        
        return jsonify({
            'success': True,
            'alert_id': alert.id,
            'message': 'Fire report submitted successfully'
        })
        
    except Exception as e:
        logger.error(f"Error creating community fire report: {e}")
        return jsonify({'error': 'Failed to submit fire report'}), 500

@app.route('/api/alerts/<int:alert_id>/resolve', methods=['POST'])
def resolve_alert(alert_id):
    """Resolve an alert"""
    try:
        alert = Alert.query.get_or_404(alert_id)
        alert.status = AlertStatus.RESOLVED
        alert.resolved_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Alert resolved successfully'})
        
    except Exception as e:
        logger.error(f"Error resolving alert {alert_id}: {e}")
        return jsonify({'error': 'Failed to resolve alert'}), 500

@app.route('/api/alerts/<int:alert_id>/navigation')
def get_alert_navigation(alert_id):
    """Get navigation information for an alert"""
    try:
        responder_location = request.args.get('location')
        if not responder_location:
            return jsonify({'error': 'Responder location required'}), 400
        
        navigation_info = get_navigation_to_alert(alert_id, responder_location)
        
        if navigation_info:
            return jsonify(navigation_info)
        else:
            return jsonify({'error': 'Could not get navigation information'}), 404
            
    except Exception as e:
        logger.error(f"Error getting navigation for alert {alert_id}: {e}")
        return jsonify({'error': 'Navigation service unavailable'}), 500

@app.route('/api/sensors')
def get_sensors():
    """Get all sensors with their current status"""
    sensors = Sensor.query.filter_by(is_active=True).all()
    
    sensor_data = []
    for sensor in sensors:
        # Get latest reading
        latest_reading = SensorReading.query.filter_by(sensor_id=sensor.id)\
                                           .order_by(SensorReading.timestamp.desc())\
                                           .first()
        
        sensor_info = {
            'id': sensor.id,
            'name': sensor.name,
            'type': sensor.sensor_type.value,
            'location': sensor.location,
            'latitude': sensor.latitude,
            'longitude': sensor.longitude,
            'threshold': sensor.threshold_value,
            'last_reading': sensor.last_reading,
            'last_update': sensor.last_update.isoformat() if sensor.last_update else None,
            'is_online': (datetime.utcnow() - sensor.last_update).total_seconds() < 300 if sensor.last_update else False,
            'latest_reading': {
                'value': latest_reading.value,
                'timestamp': latest_reading.timestamp.isoformat()
            } if latest_reading else None
        }
        sensor_data.append(sensor_info)
    
    return jsonify(sensor_data)

@app.route('/api/alerts')
def get_alerts():
    """Get alerts with optional filtering"""
    status_filter = request.args.get('status')
    limit = int(request.args.get('limit', 50))
    
    query = Alert.query
    
    if status_filter:
        query = query.filter_by(status=AlertStatus(status_filter))
    
    alerts = query.order_by(Alert.created_at.desc()).limit(limit).all()
    
    alert_data = []
    for alert in alerts:
        alert_info = {
            'id': alert.id,
            'title': alert.title,
            'description': alert.description,
            'type': alert.alert_type.value,
            'status': alert.status.value,
            'severity': alert.severity,
            'latitude': alert.latitude,
            'longitude': alert.longitude,
            'address': alert.address,
            'created_at': alert.created_at.isoformat(),
            'resolved_at': alert.resolved_at.isoformat() if alert.resolved_at else None,
            'sensor_reading': alert.sensor_reading,
            'sensor_name': alert.sensor.name if alert.sensor else None
        }
        alert_data.append(alert_info)
    
    return jsonify(alert_data)

@app.route('/api/test-sensor/<int:sensor_id>')
def test_sensor(sensor_id):
    """Test a sensor with a simulated reading"""
    try:
        test_value = float(request.args.get('value', 100))  # Default high test value
        
        if test_sensor_reading(sensor_id, test_value):
            return jsonify({
                'success': True,
                'message': f'Test reading {test_value} sent to sensor {sensor_id}'
            })
        else:
            return jsonify({'error': 'Sensor not found'}), 404
            
    except Exception as e:
        logger.error(f"Error testing sensor {sensor_id}: {e}")
        return jsonify({'error': 'Failed to test sensor'}), 500

@app.route('/api/test-notifications')
def test_notifications():
    """Test the notification system"""
    try:
        success = send_test_notifications()
        
        if success:
            return jsonify({'success': True, 'message': 'Test notifications sent'})
        else:
            return jsonify({'error': 'Failed to send test notifications'}), 500
            
    except Exception as e:
        logger.error(f"Error sending test notifications: {e}")
        return jsonify({'error': 'Test notification failed'}), 500

@app.route('/api/fire-stations')
def get_fire_stations():
    """Get nearby fire stations for given coordinates"""
    try:
        latitude = float(request.args.get('lat'))
        longitude = float(request.args.get('lng'))
        
        fire_stations = find_fire_stations(latitude, longitude)
        
        return jsonify(fire_stations)
        
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid coordinates'}), 400
    except Exception as e:
        logger.error(f"Error finding fire stations: {e}")
        return jsonify({'error': 'Fire station service unavailable'}), 500

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('base.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('base.html'), 500

# Initialize sensor monitoring on startup
def initialize_monitoring():
    """Initialize sensor monitoring when the app starts"""
    try:
        from sensor_reader import start_sensor_monitoring
        import threading
        
        # Start sensor monitoring in a separate thread
        monitor_thread = threading.Thread(target=start_sensor_monitoring)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        logger.info("Sensor monitoring initialized")
    except Exception as e:
        logger.error(f"Error initializing sensor monitoring: {e}")

# Call initialization function
initialize_monitoring()
