import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from twilio.rest import Client
from app import app, db
from models import Alert, EmergencyContact

logger = logging.getLogger(__name__)

# Twilio configuration
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.environ.get("TWILIO_PHONE_NUMBER")

# Email configuration
SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
EMAIL_ADDRESS = os.environ.get("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")

def send_sms_alert(phone_number, message):
    """Send SMS alert using Twilio"""
    try:
        if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER]):
            logger.warning("Twilio credentials not configured")
            return False
            
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        message = client.messages.create(
            body=message,
            from_=TWILIO_PHONE_NUMBER,
            to=phone_number
        )
        
        logger.info(f"SMS sent successfully to {phone_number}. SID: {message.sid}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending SMS to {phone_number}: {e}")
        return False

def send_email_alert(email_address, subject, message):
    """Send email alert using SMTP"""
    try:
        if not all([EMAIL_ADDRESS, EMAIL_PASSWORD]):
            logger.warning("Email credentials not configured")
            return False
            
        # Create message
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = email_address
        msg['Subject'] = subject
        
        # Add body to email
        msg.attach(MIMEText(message, 'plain'))
        
        # Setup SMTP server
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        
        # Send email
        text = msg.as_string()
        server.sendmail(EMAIL_ADDRESS, email_address, text)
        server.quit()
        
        logger.info(f"Email sent successfully to {email_address}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending email to {email_address}: {e}")
        return False

def send_alert_notifications(alert_id):
    """Send all notifications for a given alert"""
    try:
        with app.app_context():
            alert = Alert.query.get(alert_id)
            if not alert:
                logger.error(f"Alert {alert_id} not found")
                return
            
            # Get all active emergency contacts
            contacts = EmergencyContact.query.filter_by(is_active=True).all()
            
            if not contacts:
                logger.warning("No emergency contacts configured")
                return
            
            # Create notification messages
            sms_message = create_sms_message(alert)
            email_subject = f"🚨 FIRE ALERT - {alert.severity.upper()}"
            email_message = create_email_message(alert)
            
            sms_success = False
            email_success = False
            
            # Send notifications to all contacts
            for contact in contacts:
                if contact.phone:
                    try:
                        if send_sms_alert(contact.phone, sms_message):
                            sms_success = True
                    except Exception as e:
                        logger.error(f"Error sending SMS to {contact.name}: {e}")
                
                if contact.email:
                    try:
                        if send_email_alert(contact.email, email_subject, email_message):
                            email_success = True
                    except Exception as e:
                        logger.error(f"Error sending email to {contact.name}: {e}")
            
            # Update alert notification status
            alert.sms_sent = sms_success
            alert.email_sent = email_success
            db.session.commit()
            
            logger.info(f"Notifications sent for alert {alert_id} - SMS: {sms_success}, Email: {email_success}")
            
    except Exception as e:
        logger.error(f"Error sending alert notifications: {e}")

def create_sms_message(alert):
    """Create SMS message for alert"""
    location_info = ""
    if alert.address:
        location_info = f" at {alert.address}"
    elif alert.latitude and alert.longitude:
        location_info = f" at coordinates {alert.latitude:.4f}, {alert.longitude:.4f}"
    
    message = f"🚨 FIRE ALERT - {alert.severity.upper()}\n"
    message += f"{alert.title}{location_info}\n"
    message += f"Time: {alert.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
    
    if alert.sensor_reading:
        message += f"Sensor Reading: {alert.sensor_reading:.2f}\n"
    
    message += "Respond immediately!"
    
    return message

def create_email_message(alert):
    """Create email message for alert"""
    location_info = "Unknown location"
    if alert.address:
        location_info = alert.address
    elif alert.latitude and alert.longitude:
        location_info = f"Coordinates: {alert.latitude:.6f}, {alert.longitude:.6f}"
    
    message = f"""
FIRE ALERT NOTIFICATION

Alert Details:
- Title: {alert.title}
- Severity: {alert.severity.upper()}
- Type: {alert.alert_type.value.replace('_', ' ').title()}
- Location: {location_info}
- Time: {alert.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}

Description:
{alert.description or 'No additional description provided.'}
"""
    
    if alert.sensor_reading:
        message += f"\nSensor Reading: {alert.sensor_reading:.2f}"
    
    if alert.sensor:
        message += f"\nSensor: {alert.sensor.name} ({alert.sensor.sensor_type.value})"
        message += f"\nThreshold: {alert.sensor.threshold_value:.2f}"
    
    message += """

IMMEDIATE ACTION REQUIRED:
1. Verify the alert location
2. Dispatch emergency responders
3. Coordinate with local fire department
4. Monitor the situation until resolved

This is an automated alert from the Fire Response and Monitoring System.
"""
    
    return message

def send_test_notifications():
    """Send test notifications to verify system functionality"""
    try:
        with app.app_context():
            contacts = EmergencyContact.query.filter_by(is_active=True).first()
            
            if not contacts:
                logger.warning("No emergency contacts found for testing")
                return False
            
            test_message = "🔥 TEST ALERT: Fire monitoring system is operational. This is a test message."
            
            success = True
            if contacts.phone:
                success &= send_sms_alert(contacts.phone, test_message)
            
            if contacts.email:
                success &= send_email_alert(
                    contacts.email,
                    "Fire Monitoring System - Test Alert",
                    test_message
                )
            
            return success
            
    except Exception as e:
        logger.error(f"Error sending test notifications: {e}")
        return False
