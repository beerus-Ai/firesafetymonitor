# Updated location step to encourage live location sharing
import os
import logging
from flask import request, jsonify
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from app import app, db
from models import Alert, AlertType, AlertStatus
from notifier import send_alert_notifications
from gps_navigator import geocode_address, reverse_geocode
import re
import threading

logger = logging.getLogger(__name__)

# Twilio WhatsApp configuration
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.environ.get("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")  # Twilio Sandbox number

# Initialize Twilio client
twilio_client = None
if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
    twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# User session storage for multi-step conversations
user_sessions = {}

class FireReportSession:
    def __init__(self, phone_number):
        self.phone_number = phone_number
        self.step = "initial"
        self.data = {}
        self.last_activity = None

    def reset(self):
        self.step = "initial"
        self.data = {}

def send_whatsapp_message(to_number, message):
    """Send WhatsApp message using Twilio"""
    if not twilio_client:
        logger.error("Twilio client not configured for WhatsApp")
        return False

    try:
        message = twilio_client.messages.create(
            body=message,
            from_=TWILIO_WHATSAPP_NUMBER,
            to=f"whatsapp:{to_number}"
        )
        logger.info(f"WhatsApp message sent to {to_number}. SID: {message.sid}")
        return True
    except Exception as e:
        logger.error(f"Error sending WhatsApp message to {to_number}: {e}")
        return False

def parse_location_from_message(message):
    """Extract location information from user message"""
    # Look for coordinates pattern (latitude, longitude)
    coord_pattern = r'(-?\d+\.?\d*),\s*(-?\d+\.?\d*)'
    coord_match = re.search(coord_pattern, message)

    if coord_match:
        try:
            lat = float(coord_match.group(1))
            lng = float(coord_match.group(2))
            if -90 <= lat <= 90 and -180 <= lng <= 180:
                return {"latitude": lat, "longitude": lng, "type": "coordinates"}
        except ValueError:
            pass

    # Look for address indicators
    address_keywords = ["at", "near", "on", "address", "location", "street", "avenue", "road", "building"]
    message_lower = message.lower()

    for keyword in address_keywords:
        if keyword in message_lower:
            # Extract text after the keyword as potential address
            parts = message_lower.split(keyword, 1)
            if len(parts) > 1:
                address = parts[1].strip()
                if len(address) > 3:  # Reasonable address length
                    return {"address": address, "type": "address"}

    # If no specific indicators, treat the whole message as potential address
    if len(message.strip()) > 5:
        return {"address": message.strip(), "type": "address"}

    return None

def determine_severity_from_message(message):
    """Determine fire severity from user description"""
    message_lower = message.lower()

    # Critical severity indicators
    critical_words = ["explosion", "huge", "massive", "spreading fast", "trapped", "emergency", "help", "danger"]
    if any(word in message_lower for word in critical_words):
        return "critical"

    # High severity indicators
    high_words = ["large", "big", "growing", "smoke everywhere", "multiple", "building"]
    if any(word in message_lower for word in high_words):
        return "high"

    # Low severity indicators
    low_words = ["small", "contained", "minor", "little", "under control"]
    if any(word in message_lower for word in low_words):
        return "low"

    # Default to medium
    return "medium"

def process_whatsapp_message(from_number, message_body, is_location_share=False):
    """Process incoming WhatsApp message and handle fire reporting conversation"""

    # Clean phone number
    phone_number = from_number.replace("whatsapp:", "")

    # Get or create user session
    if phone_number not in user_sessions:
        user_sessions[phone_number] = FireReportSession(phone_number)

    session = user_sessions[phone_number]
    message_lower = message_body.lower().strip()

    # Handle commands that reset session
    if message_lower in ["start", "begin", "report fire", "fire", "emergency", "help"]:
        session.reset()
        session.step = "greeting"

        response = """🚨 *Fire Emergency Reporting System*

I'm here to help you report a fire emergency quickly and efficiently.

Please choose an option:
1️⃣ Report a new fire emergency
2️⃣ Get emergency contact information
3️⃣ Get fire safety tips

Type the number of your choice or say "fire" to report immediately."""

        return response

    # Handle main conversation flow
    if session.step == "initial" or session.step == "greeting":
        if message_lower in ["1", "fire", "report", "emergency"]:
            session.step = "location"
            return """📍 *Location Information Needed*

**PREFERRED:** 🗺️ Share your live location by:
1. Tap the 📎 attachment button
2. Select "Location" 
3. Choose "Share Live Location" or "Send Your Current Location"

**OR provide location by:**
📝 Send coordinates: latitude, longitude (e.g., 40.7128, -74.0060)
🏠 Describe the address or nearby landmarks

Example: "123 Main Street" or "Near Central Park entrance"

*Live location sharing gives emergency responders the most accurate location data!*"""

        elif message_lower in ["2", "contact", "contacts"]:
            return """📞 *Emergency Contacts*

🚨 **IMMEDIATE EMERGENCY: CALL 911**

🔥 Fire Department: 911
🚑 Emergency Services: 911
👮 Police: 911

💬 You can also continue reporting through this WhatsApp bot for additional coordination."""

        elif message_lower in ["3", "safety", "tips"]:
            return """🛡️ *Fire Safety Tips*

**If you see a fire:**
✅ Call 911 first
✅ Alert others nearby
✅ Evacuate safely
✅ Meet at designated safe area
✅ Stay low if there's smoke

**DO NOT:**
❌ Use elevators
❌ Go back inside
❌ Fight large fires yourself
❌ Panic

Type "fire" to report an emergency now."""

        else:
            return """Please choose an option:
1️⃣ Report fire emergency
2️⃣ Emergency contacts
3️⃣ Fire safety tips

Or type "fire" to report immediately."""

    elif session.step == "location":
        # Handle WhatsApp location sharing
        if is_location_share:
            # Parse coordinates from shared location
            coord_pattern = r'(-?\d+\.?\d*),\s*(-?\d+\.?\d*)'
            coord_match = re.search(coord_pattern, message_body)
            
            if coord_match:
                try:
                    lat = float(coord_match.group(1))
                    lng = float(coord_match.group(2))
                    if -90 <= lat <= 90 and -180 <= lng <= 180:
                        session.data["location"] = {"latitude": lat, "longitude": lng, "type": "coordinates"}
                        session.step = "description"
                        
                        return """✅ *Location Received!*

📍 Your live location has been captured successfully.

🔥 *Now describe the fire:*
- Size of the fire (small, medium, large)
- What's burning (building, car, etc.)
- Color of smoke
- Are people in danger?
- Any other important details

Be as specific as possible to help emergency responders."""
                except ValueError:
                    pass
        
        # Handle text-based location input
        location_info = parse_location_from_message(message_body)

        if location_info:
            session.data["location"] = location_info
            session.step = "description"

            return """🔥 *Describe the Fire*

Please describe what you see:
- Size of the fire (small, medium, large)
- What's burning (building, car, etc.)
- Color of smoke
- Are people in danger?
- Any other important details

Be as specific as possible to help emergency responders."""

        else:
            return """❌ I couldn't understand the location. Please try again:

📝 Send coordinates: 40.7128, -74.0060
🏠 Send address: 123 Main Street, City
📍 Or share your live location using the 📎 attachment button → Location"""

    elif session.step == "description":
        session.data["description"] = message_body
        session.data["severity"] = determine_severity_from_message(message_body)
        session.step = "contact_info"

        return """👤 *Your Contact Information (Optional)*

Please provide your name and phone number so emergency responders can contact you if needed:

Example: "John Smith, +1234567890"

Or type "skip" to submit the report anonymously."""

    elif session.step == "contact_info":
        if message_lower != "skip":
            # Try to parse name and phone from message
            parts = message_body.split(",")
            if len(parts) >= 2:
                session.data["reporter_name"] = parts[0].strip()
                session.data["reporter_phone"] = parts[1].strip()
            else:
                session.data["reporter_name"] = message_body.strip()
                session.data["reporter_phone"] = phone_number

        # Create the fire alert
        try:
            alert_created = create_fire_alert_from_whatsapp(session.data, phone_number)

            if alert_created:
                session.reset()
                return """✅ *Fire Report Submitted Successfully!*

🚨 Alert ID: #{alert_id}
📞 Emergency responders have been notified
📱 SMS alerts sent to fire department
📍 Location confirmed and logged

**IMPORTANT:** If this is an active emergency, please also CALL 911 immediately.

Thank you for using our fire reporting system. Stay safe!

Type "start" to report another emergency.""".replace("{alert_id}", str(alert_created))

            else:
                session.reset()
                return """❌ *Error Submitting Report*

There was a technical issue submitting your fire report. 

**PLEASE CALL 911 IMMEDIATELY** if this is an active emergency.

You can try reporting again by typing "start"."""

        except Exception as e:
            logger.error(f"Error creating WhatsApp fire alert: {e}")
            session.reset()
            return """❌ *System Error*

Unable to process your report due to a system error.

**CALL 911 IMMEDIATELY** for emergency assistance.

Technical support has been notified."""

    # Handle unknown messages
    return """I didn't understand that message. 

Type "start" to begin fire reporting
Type "help" for assistance
Type "fire" for immediate emergency reporting

For immediate emergencies, CALL 911."""

def create_fire_alert_from_whatsapp(session_data, reporter_phone):
    """Create fire alert from WhatsApp conversation data"""
    try:
        with app.app_context():
            location_info = session_data.get("location", {})

            # Handle location data
            latitude = None
            longitude = None
            address = None

            if location_info.get("type") == "coordinates":
                latitude = location_info["latitude"]
                longitude = location_info["longitude"]
                # Try to get address from coordinates
                address = reverse_geocode(latitude, longitude)
            elif location_info.get("type") == "address":
                address = location_info["address"]
                # Try to get coordinates from address
                coords = geocode_address(address)
                if coords and len(coords) == 2:
                    latitude, longitude = coords

            # Create alert
            alert = Alert(
                title="WhatsApp Fire Report",
                description=session_data.get("description", "Fire reported via WhatsApp"),
                alert_type=AlertType.COMMUNITY_REPORT,
                status=AlertStatus.ACTIVE,
                severity=session_data.get("severity", "medium"),
                latitude=latitude or 0.0,
                longitude=longitude or 0.0,
                address=address,
                reporter_name=session_data.get("reporter_name"),
                reporter_phone=session_data.get("reporter_phone", reporter_phone),
                reporter_email=None
            )

            db.session.add(alert)
            db.session.commit()

            # Send notifications to emergency responders
            notification_thread = threading.Thread(target=send_alert_notifications, args=(alert.id,))
            notification_thread.daemon = True
            notification_thread.start()

            logger.info(f"Fire alert created from WhatsApp: {alert.id}")
            return alert.id

    except Exception as e:
        logger.error(f"Error creating fire alert from WhatsApp: {e}")
        return None

@app.route('/webhook/whatsapp', methods=['POST'])
def whatsapp_webhook():
    """Handle incoming WhatsApp messages from Twilio"""
    try:
        # Get message data from Twilio
        from_number = request.form.get('From', '')
        message_body = request.form.get('Body', '').strip()
        
        # Check for WhatsApp location sharing
        latitude = request.form.get('Latitude')
        longitude = request.form.get('Longitude')
        
        logger.info(f"Received WhatsApp message from {from_number}: {message_body}")
        if latitude and longitude:
            logger.info(f"Location shared: {latitude}, {longitude}")

        # Handle location sharing
        if latitude and longitude:
            try:
                lat = float(latitude)
                lng = float(longitude)
                location_message = f"{lat}, {lng}"
                response_text = process_whatsapp_message(from_number, location_message, is_location_share=True)
            except ValueError:
                logger.error(f"Invalid location coordinates: {latitude}, {longitude}")
                response_text = process_whatsapp_message(from_number, message_body)
        else:
            # Process regular text message
            response_text = process_whatsapp_message(from_number, message_body)

        # Create Twilio response
        response = MessagingResponse()
        response.message(response_text)

        logger.info(f"Sent WhatsApp response to {from_number}")

        return str(response), 200, {'Content-Type': 'text/xml'}

    except Exception as e:
        logger.error(f"Error processing WhatsApp webhook: {e}")

        # Send error response
        response = MessagingResponse()
        response.message("Sorry, there was an error processing your message. For emergencies, please call 911.")

        return str(response), 200, {'Content-Type': 'text/xml'}

@app.route('/api/whatsapp/send-alert', methods=['POST'])
def send_whatsapp_alert():
    """Send WhatsApp alert to specific number (for testing)"""
    try:
        data = request.get_json()
        to_number = data.get('to_number')
        message = data.get('message')

        if not to_number or not message:
            return jsonify({'error': 'Missing to_number or message'}), 400

        success = send_whatsapp_message(to_number, message)

        if success:
            return jsonify({'success': True, 'message': 'WhatsApp alert sent'})
        else:
            return jsonify({'error': 'Failed to send WhatsApp message'}), 500

    except Exception as e:
        logger.error(f"Error sending WhatsApp alert: {e}")
        return jsonify({'error': 'Failed to send WhatsApp alert'}), 500

@app.route('/api/whatsapp/test', methods=['POST'])
def test_whatsapp_bot():
    """Test WhatsApp bot functionality"""
    try:
        data = request.get_json()
        test_number = data.get('phone_number', '+1234567890')

        # Send test message
        test_message = """🔥 Fire Emergency System Test

This is a test of the WhatsApp fire reporting system.

Type "start" to begin fire emergency reporting.

For real emergencies, always call 911 first!"""

        success = send_whatsapp_message(test_number, test_message)

        if success:
            return jsonify({
                'success': True, 
                'message': 'Test message sent to WhatsApp',
                'phone_number': test_number
            })
        else:
            return jsonify({'error': 'Failed to send test message'}), 500

    except Exception as e:
        logger.error(f"Error testing WhatsApp bot: {e}")
        return jsonify({'error': 'WhatsApp test failed'}), 500