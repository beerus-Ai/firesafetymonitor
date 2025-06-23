#!/usr/bin/env python3
"""
WhatsApp Fire Reporting Bot Demonstration
Simulates WhatsApp conversations and creates sample fire reports
"""

from app import app, db
from models import Alert, AlertType, AlertStatus
from whatsapp_bot import process_whatsapp_message, create_fire_alert_from_whatsapp
import time

def simulate_whatsapp_conversation():
    """Simulate a complete WhatsApp fire reporting conversation"""
    
    print("🔥 WhatsApp Fire Reporting Bot Simulation")
    print("=" * 50)
    
    # Test phone number
    test_phone = "+1234567890"
    
    # Conversation flow
    conversations = [
        # Conversation 1: Complete fire report
        {
            "name": "Emergency Building Fire Report",
            "messages": [
                "fire",
                "1",
                "123 Main Street, downtown near the bank",
                "Large fire on the second floor of office building. Heavy black smoke coming from windows. Multiple people evacuated but some may still be inside. Fire spreading quickly!",
                "John Smith, +1234567890"
            ]
        },
        # Conversation 2: Coordinates-based report
        {
            "name": "Warehouse Fire with Coordinates",
            "messages": [
                "emergency",
                "1",
                "40.7128, -74.0060",
                "Small fire in warehouse storage area. Contained to one corner. No people in danger. Chemical smell in smoke.",
                "skip"
            ]
        },
        # Conversation 3: Information request
        {
            "name": "Safety Information Request",
            "messages": [
                "start",
                "3"
            ]
        }
    ]
    
    for i, conversation in enumerate(conversations, 1):
        print(f"\n🗨️  Conversation {i}: {conversation['name']}")
        print("-" * 40)
        
        # Reset user session for each conversation
        from whatsapp_bot import user_sessions
        if test_phone in user_sessions:
            user_sessions[test_phone].reset()
        
        for j, message in enumerate(conversation['messages'], 1):
            print(f"\n👤 User message {j}: {message}")
            
            # Process message
            response = process_whatsapp_message(f"whatsapp:{test_phone}", message)
            
            print(f"🤖 Bot response:")
            print(response)
            
            # Add delay to simulate real conversation
            time.sleep(0.5)
        
        print(f"\n✅ Conversation {i} completed")
        time.sleep(1)

def create_sample_whatsapp_reports():
    """Create sample WhatsApp fire reports in the database"""
    
    print("\n📊 Creating Sample WhatsApp Fire Reports")
    print("=" * 50)
    
    sample_reports = [
        {
            "location": {"latitude": 40.7128, "longitude": -74.0060, "type": "coordinates"},
            "description": "Kitchen fire in apartment building. Smoke alarm triggered. Residents evacuating. Fire department needed urgently!",
            "severity": "high",
            "reporter_name": "Maria Garcia",
            "reporter_phone": "+1555123456"
        },
        {
            "location": {"address": "Central Park West, near playground", "type": "address"},
            "description": "Small brush fire near children's playground. Wind picking up. Need immediate response before it spreads.",
            "severity": "medium",
            "reporter_name": "David Chen",
            "reporter_phone": "+1555987654"
        },
        {
            "location": {"latitude": 40.7505, "longitude": -73.9934, "type": "coordinates"},
            "description": "Car fire in parking garage. Vehicle fully engulfed. Other cars nearby at risk. Explosion possible.",
            "severity": "critical",
            "reporter_name": "Anonymous",
            "reporter_phone": "+1555000000"
        },
        {
            "location": {"address": "Industrial District, Building 42", "type": "address"},
            "description": "Electrical fire in factory. Power grid affected. Workers safely evacuated. Smoke visible from street.",
            "severity": "high",
            "reporter_name": "Safety Officer Thompson",
            "reporter_phone": "+1555456789"
        },
        {
            "location": {"latitude": 40.7282, "longitude": -74.0776, "type": "coordinates"},
            "description": "Trash can fire outside school. Small but could spread to building. Students are inside for classes.",
            "severity": "low",
            "reporter_name": "Teacher Johnson",
            "reporter_phone": "+1555111222"
        }
    ]
    
    with app.app_context():
        for i, report_data in enumerate(sample_reports, 1):
            try:
                alert_id = create_fire_alert_from_whatsapp(report_data, report_data["reporter_phone"])
                
                if alert_id:
                    print(f"✅ Created WhatsApp report #{alert_id}: {report_data['description'][:50]}...")
                else:
                    print(f"❌ Failed to create report {i}")
                    
            except Exception as e:
                print(f"❌ Error creating report {i}: {e}")
        
        # Show statistics
        whatsapp_alerts = Alert.query.filter_by(title="WhatsApp Fire Report").count()
        total_alerts = Alert.query.count()
        
        print(f"\n📈 Report Statistics:")
        print(f"   WhatsApp Reports: {whatsapp_alerts}")
        print(f"   Total Fire Alerts: {total_alerts}")
        print(f"   Success Rate: {(whatsapp_alerts/len(sample_reports)*100):.1f}%")

def demonstrate_bot_features():
    """Demonstrate key WhatsApp bot features"""
    
    print("\n🚀 WhatsApp Bot Features Demonstration")
    print("=" * 50)
    
    features = [
        {
            "name": "Multi-language Support",
            "description": "Bot responds to 'fire', 'emergency', 'help', 'start'",
            "test_messages": ["fire", "emergency", "help", "start"]
        },
        {
            "name": "Location Intelligence", 
            "description": "Accepts coordinates, addresses, and landmarks",
            "test_messages": ["40.7128, -74.0060", "123 Main Street", "near Central Park"]
        },
        {
            "name": "Severity Detection",
            "description": "Automatically determines fire severity from description",
            "test_messages": [
                "huge explosion, people trapped!",  # Critical
                "large building fire spreading",    # High  
                "small kitchen fire contained",     # Low
                "moderate smoke from car"           # Medium
            ]
        },
        {
            "name": "Safety Information",
            "description": "Provides emergency contacts and safety tips",
            "test_messages": ["2", "3"]  # Menu options
        }
    ]
    
    test_phone = "+1234567890"
    
    for feature in features:
        print(f"\n🔧 Feature: {feature['name']}")
        print(f"📝 {feature['description']}")
        
        for test_msg in feature['test_messages'][:2]:  # Limit to 2 examples
            try:
                response = process_whatsapp_message(f"whatsapp:{test_phone}", test_msg)
                print(f"   Input: '{test_msg}' → Response: {response[:100]}...")
            except Exception as e:
                print(f"   Input: '{test_msg}' → Error: {e}")

def show_integration_info():
    """Show WhatsApp integration setup information"""
    
    print("\n🔗 WhatsApp Integration Setup")
    print("=" * 50)
    
    setup_steps = [
        "1. Twilio Account Setup",
        "   - Create Twilio account at twilio.com",
        "   - Get Account SID and Auth Token",
        "   - Add to environment variables",
        "",
        "2. WhatsApp Sandbox Configuration", 
        "   - Go to Twilio Console → Messaging → Try it out",
        "   - Follow WhatsApp sandbox setup instructions",
        "   - Connect your phone number to sandbox",
        "",
        "3. Webhook Configuration",
        "   - Set webhook URL to: https://your-app.replit.app/webhook/whatsapp",
        "   - Configure HTTP POST method",
        "   - Test webhook connectivity",
        "",
        "4. Production Setup (Optional)",
        "   - Apply for WhatsApp Business API",
        "   - Get approved phone number",
        "   - Configure production webhooks"
    ]
    
    for step in setup_steps:
        print(step)
    
    print(f"\n📱 Test Bot Commands:")
    commands = [
        "'fire' or 'emergency' - Start fire reporting",
        "'start' - Show main menu",
        "'help' - Get assistance", 
        "'2' - Emergency contact information",
        "'3' - Fire safety tips"
    ]
    
    for cmd in commands:
        print(f"   {cmd}")

if __name__ == "__main__":
    print("🔥 WhatsApp Fire Response Bot - Complete Demonstration")
    print("=" * 60)
    
    # Run all demonstrations
    simulate_whatsapp_conversation()
    create_sample_whatsapp_reports() 
    demonstrate_bot_features()
    show_integration_info()
    
    print(f"\n🎉 WhatsApp Bot Demonstration Complete!")
    print("The bot is ready for community fire reporting via WhatsApp.")
    print("Visit /whatsapp-bot in the web interface for management tools.")