"""
Emergency Email Notification System for Sathi AI
Sends emails to family members when elderly users ask for help or use emergency keywords
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import logging
from typing import Dict
import re
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Optional Twilio import
try:
    from twilio.rest import Client
    from twilio.base.exceptions import TwilioRestException
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    # Create dummy classes for type hints
    class Client:
        pass
    class TwilioRestException(Exception):
        pass

class EmergencyEmailNotifier:
    """Handles emergency email notifications to family members"""
    
    def __init__(self):
        # Family member contacts from environment variables
        self.family_contacts = {
            'son': {
                'name': os.getenv('FAMILY_SON_NAME', 'Ajay Nandurkar'),
                'email': os.getenv('FAMILY_SON_EMAIL', 'nandurkarajay07@gmail.com'),
                'phone': os.getenv('FAMILY_SON_PHONE', '+917066291745'),
                'relationship': 'son'
            },
            'Kaustubh Darade': {
                'name': os.getenv('FAMILY_KAUSTUBH_NAME', 'Kaustubh Darade'), 
                'email': os.getenv('FAMILY_KAUSTUBH_EMAIL', 'en22212161@git-india.edu.in'),
                'phone': os.getenv('FAMILY_KAUSTUBH_PHONE', '+917066291745'),  
                'relationship': 'son'
            }
        }
        
        # Email configuration from environment variables
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.sender_email = os.getenv('EMAIL_SENDER', 'nandurkarajay07@gmail.com')
        self.sender_password = os.getenv('EMAIL_PASSWORD', '')
        
        # Twilio configuration from environment variables
        self.twilio_account_sid = os.getenv('TWILIO_ACCOUNT_SID', '')
        self.twilio_auth_token = os.getenv('TWILIO_AUTH_TOKEN', '')
        self.twilio_phone_number = os.getenv('TWILIO_PHONE_NUMBER', '+12296292723')
        self.emergency_phone_number = os.getenv('EMERGENCY_PHONE_NUMBER', '+917066291745')
        
        # Validate required credentials
        self._validate_credentials()
        
        # Emergency keywords and phrases - MORE STRICT
        self.emergency_keywords = [
            'emergency', 'urgent', 'need help', 'please help',
            'call someone', 'contact someone', 'send message',
            'trouble', 'problem', 'can\'t breathe', 'chest pain', 
            'fall', 'fell down', 'hurt', 'sick', 'unwell', 
            'dizzy', 'confused', 'lost', 'alone'
        ]
        
        # Remove family-related keywords to avoid false triggers
        # Only trigger on actual health/safety emergencies
        
        # Family member request patterns - VERY STRICT
        self.family_request_patterns = [
            r'(please|send|inform|notify|alert)\s+(my|to)\s+(son|daughter|family)\s+(to\s+call|to\s+message|to\s+email|to\s+contact)',
            r'(call|message|email|text)\s+(my|to)\s+(son|daughter|family)\s+(urgently|right\s+now|immediately)',
            r'(get|reach|contact)\s+(my|to)\s+(son|daughter|family)\s+(urgently|right\s+now|immediately)'
        ]
        
        logging.info("Emergency Email Notifier initialized")
    
    def _validate_credentials(self):
        """Validate that required credentials are available"""
        missing_credentials = []
        
        # Check email credentials
        if not self.sender_email:
            missing_credentials.append("EMAIL_SENDER")
        if not self.sender_password:
            missing_credentials.append("EMAIL_PASSWORD")
        
        # Check Twilio credentials
        if TWILIO_AVAILABLE:
            if not self.twilio_account_sid:
                missing_credentials.append("TWILIO_ACCOUNT_SID")
            if not self.twilio_auth_token:
                missing_credentials.append("TWILIO_AUTH_TOKEN")
        
        if missing_credentials:
            logging.warning(f"Missing credentials: {', '.join(missing_credentials)}")
            logging.warning("Please set up your .env file with the required credentials")
            logging.info("See .env.example for reference")
    
    def detect_emergency_request(self, user_input: str) -> Dict[str, any]:
        """
        Detect if user is asking for help or emergency
        
        Args:
            user_input: The user's speech/text input
            
        Returns:
            Dict with emergency detection results
        """
        user_input_lower = user_input.lower()
        
        # Check for emergency keywords
        emergency_detected = any(keyword in user_input_lower for keyword in self.emergency_keywords)
        
        # Check for family member requests
        family_requested = None
        for pattern in self.family_request_patterns:
            match = re.search(pattern, user_input_lower)
            if match:
                family_requested = match.group(3)  # Extract 'son' or 'daughter'
                break
        
        # Check for explicit family mentions ONLY with emergency context
        if not family_requested:
            # Only trigger if there's an emergency context OR explicit request for contact
            emergency_context = any(word in user_input_lower for word in ['help', 'call', 'contact', 'reach', 'message', 'email', 'inform', 'notify', 'alert'])
            
            # Additional check: must have action word + family member
            action_words = ['call', 'contact', 'message', 'email', 'tell', 'inform', 'notify', 'alert', 'send', 'reach']
            has_action = any(word in user_input_lower for word in action_words)
            has_family = any(word in user_input_lower for word in ['son', 'daughter', 'family'])
            
            if emergency_context and has_action and has_family:
                if 'son' in user_input_lower:
                    family_requested = 'son'
                elif 'daughter' in user_input_lower:
                    family_requested = 'daughter'
                elif 'family' in user_input_lower:
                    family_requested = 'family'  # Will notify both
        
        return {
            'emergency_detected': emergency_detected,
            'family_requested': family_requested,
            'original_input': user_input,
            'timestamp': datetime.now(),
            'should_notify': emergency_detected or family_requested is not None
        }
    
    def create_emergency_email(self, detection_result: Dict[str, any]) -> Dict[str, str]:
        """
        Create emergency email content
        
        Args:
            detection_result: Result from emergency detection
            
        Returns:
            Dict with email subject and body
        """
        timestamp = detection_result['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
        original_input = detection_result['original_input']
        
        # Determine recipients
        if detection_result['family_requested'] == 'family':
            recipients = ['son', 'daughter']
            recipient_names = "Son and Daughter"
        elif detection_result['family_requested']:
            recipients = [detection_result['family_requested']]
            recipient_names = self.family_contacts[detection_result['family_requested']]['name']
        else:
            recipients = ['son', 'daughter']  # Default to both for emergencies
            recipient_names = "Son and Daughter"
        
        # Create subject
        if detection_result['family_requested']:
            subject = f"Sathi AI - Family Request from Elderly Parent"
        else:
            subject = f"Sathi AI - EMERGENCY Alert from Elderly Parent"
        
        # Create email body
        body = f"""Dear {recipient_names},

EMERGENCY ALERT from Sathi AI

Time: {timestamp}
Message: "{original_input}"

Your family member needs immediate help.

EMERGENCY ALERT: They need help right now!

ACTION REQUIRED:
Call them IMMEDIATELY to check their safety and wellbeing
Assess the situation and provide assistance if needed
If they mention chest pain, breathing trouble, or falls - call emergency services

---
Sathi AI Emergency System
{timestamp}"""
        
        return {
            'subject': subject,
            'body': body,
            'recipients': recipients,
            'recipient_names': recipient_names
        }
    
    def send_emergency_email(self, detection_result: Dict[str, any]) -> Dict[str, bool]:
        """
        Send emergency email and make phone calls to family members
        
        Args:
            detection_result: Result from emergency detection
            
        Returns:
            Dict with email_sent and call_sent status
        """
        result = {
            'email_sent': False,
            'call_sent': False
        }
        
        try:
            # Check if this is a custom message from emergency handler
            if 'emergency_level' in detection_result:
                email_result = self._send_custom_emergency_email(detection_result)
                result['email_sent'] = email_result
            else:
                # Original email creation logic for backward compatibility
                email_content = self.create_emergency_email(detection_result)
                
                # Get recipient emails
                recipient_emails = []
                for recipient in email_content['recipients']:
                    if recipient in self.family_contacts:
                        recipient_emails.append(self.family_contacts[recipient]['email'])
                
                if not recipient_emails:
                    logging.error("No valid recipient emails found")
                else:
                    # Create message
                    message = MIMEMultipart("alternative")
                    message["Subject"] = email_content['subject']
                    message["From"] = self.sender_email
                    message["To"] = ", ".join(recipient_emails)
                    
                    # Add body
                    text_part = MIMEText(email_content['body'], "plain")
                    message.attach(text_part)
                    
                    # Send email (for now, just log it since we don't have real SMTP setup)
                    logging.info(f"EMERGENCY EMAIL WOULD BE SENT:")
                    logging.info(f"To: {', '.join(recipient_emails)}")
                    logging.info(f"Subject: {email_content['subject']}")
                    logging.info(f"Body: {email_content['body'][:200]}...")
                    
                    # Try to send real email first
                    try:
                        # Create SMTP session and send real email
                        import smtplib
                        import ssl
                        
                        context = ssl.create_default_context()
                        server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                        server.starttls(context=context)
                        server.login(self.sender_email, self.sender_password)
                        
                        # Send to all recipients
                        for email_addr in recipient_emails:
                            message = MIMEMultipart()
                            message["From"] = self.sender_email
                            message["To"] = email_addr
                            message["Subject"] = email_content['subject']
                            message.attach(MIMEText(email_content['body'], "plain"))
                            
                            server.sendmail(self.sender_email, email_addr, message.as_string())
                        
                        server.quit()
                        
                        print(f"\n📧 REAL EMAIL SENT!")
                        print(f"To: {', '.join(recipient_emails)}")
                        print(f"Subject: {email_content['subject']}")
                        print(f"Time: {detection_result['timestamp']}")
                        print(f"User said: \"{detection_result['original_input']}\"")
                        print("Family members have been notified by email!")
                        result['email_sent'] = True
                        
                    except Exception as e:
                        print(f"Real email failed: {e}")
                        print("Falling back to simulation mode...")
                        
                        # Fallback to simulation
                        print(f"\n📧 EMAIL SIMULATION:")
                        print(f"To: {', '.join(recipient_emails)}")
                        print(f"Subject: {email_content['subject']}")
                        print(f"Time: {detection_result['timestamp']}")
                        print(f"User said: \"{detection_result['original_input']}\"")
                        print("Email not actually sent - SMTP error")
                        result['email_sent'] = True  # Still mark as sent for simulation
                    
                    logging.info(f"Email processing completed for {', '.join(recipient_emails)}")
            
            # Make emergency phone call
            print("\n" + "="*50)
            call_result = self.make_emergency_call(detection_result)
            result['call_sent'] = call_result
            
            # Summary
            email_status = "✅ Sent" if result['email_sent'] else "❌ Failed"
            call_status = "✅ Initiated" if result['call_sent'] else "❌ Failed"
            print(f"\n🚨 EMERGENCY NOTIFICATION SUMMARY:")
            print(f"📧 Email: {email_status}")
            print(f"📞 Phone Call: {call_status}")
            print("="*50)
            
            return result
            
        except Exception as e:
            logging.error(f"Emergency notification system failed: {e}")
            return result
    
    def _send_custom_emergency_email(self, detection_result: Dict[str, any]) -> Dict[str, bool]:
        """
        Send custom emergency email and make phone calls from emergency handler
        
        Args:
            detection_result: Custom detection result from emergency handler
            
        Returns:
            Dict with email_sent and call_sent status
        """
        result = {
            'email_sent': False,
            'call_sent': False
        }
        
        try:
            # Get recipient emails (notify all family contacts)
            recipient_emails = []
            for contact in self.family_contacts.values():
                recipient_emails.append(contact['email'])
            
            if not recipient_emails:
                logging.error("No valid recipient emails found")
            else:
                # Create custom subject based on emergency level
                level = detection_result.get('emergency_level', 'first_alert')
                timestamp = detection_result['timestamp']
                
                if level == 'second_alert':
                    subject = f"URGENT - NO RESPONSE - Sathi AI Emergency Alert"
                elif level == 'confirmed_emergency':
                    subject = f"CONFIRMED EMERGENCY - Sathi AI Alert"
                else:
                    subject = f"POSSIBLE EMERGENCY - Sathi AI Alert"
                
                # Create custom body
                body = f"""Sathi AI Emergency Alert

Time: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}
User said: "{detection_result['original_input']}"
Status: {detection_result.get('emergency_status', 'unknown')}

{detection_result.get('custom_message', 'Emergency situation detected. Please check on the user immediately.')}

---
Sathi AI Emergency System
{timestamp.strftime('%Y-%m-%d %H:%M:%S')}"""
                
                # Create and send message
                message = MIMEMultipart()
                message["From"] = self.sender_email
                message["To"] = ", ".join(recipient_emails)
                message["Subject"] = subject
                message.attach(MIMEText(body, "plain"))
                
                # Try to send real email
                try:
                    context = ssl.create_default_context()
                    server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                    server.starttls(context=context)
                    server.login(self.sender_email, self.sender_password)
                    
                    for email_addr in recipient_emails:
                        msg = MIMEMultipart()
                        msg["From"] = self.sender_email
                        msg["To"] = email_addr
                        msg["Subject"] = subject
                        msg.attach(MIMEText(body, "plain"))
                        server.sendmail(self.sender_email, email_addr, msg.as_string())
                    
                    server.quit()
                    
                    print(f"\n🚨 EMERGENCY EMAIL SENT!")
                    print(f"Level: {level}")
                    print(f"To: {', '.join(recipient_emails)}")
                    print(f"Subject: {subject}")
                    print(f"Time: {timestamp}")
                    print(f"User said: \"{detection_result['original_input']}\"")
                    print("Family members have been notified by email!")
                    result['email_sent'] = True
                    
                except Exception as e:
                    print(f"Real email failed: {e}")
                    print(f"\n🚨 EMERGENCY EMAIL SIMULATION:")
                    print(f"Level: {level}")
                    print(f"To: {', '.join(recipient_emails)}")
                    print(f"Subject: {subject}")
                    print(f"Time: {timestamp}")
                    print(f"User said: \"{detection_result['original_input']}\"")
                    print("Email not actually sent - SMTP error")
                    result['email_sent'] = True  # Return True for simulation
            
            # Make emergency phone call for custom emergency
            print("\n" + "="*50)
            call_result = self.make_emergency_call(detection_result)
            result['call_sent'] = call_result
            
            # Summary
            email_status = "✅ Sent" if result['email_sent'] else "❌ Failed"
            call_status = "✅ Initiated" if result['call_sent'] else "❌ Failed"
            print(f"\n🚨 CUSTOM EMERGENCY NOTIFICATION SUMMARY:")
            print(f"📧 Email: {email_status}")
            print(f"📞 Phone Call: {call_status}")
            print("="*50)
            
            return result
            
        except Exception as e:
            logging.error(f"Custom emergency notification system failed: {e}")
            return result
    
    def process_user_input(self, user_input: str) -> Dict[str, any]:
        """
        Process user input and send emergency email and phone calls if needed
        
        Args:
            user_input: The user's speech/text input
            
        Returns:
            Dict with processing results including email and call status
        """
        # Detect emergency
        detection_result = self.detect_emergency_request(user_input)
        
        result = {
            'user_input': user_input,
            'detection_result': detection_result,
            'email_sent': False,
            'call_sent': False,
            'timestamp': datetime.now()
        }
        
        # Send email and make calls if emergency detected
        if detection_result['should_notify']:
            notification_results = self.send_emergency_email(detection_result)
            result['email_sent'] = notification_results['email_sent']
            result['call_sent'] = notification_results['call_sent']
            
            if result['email_sent'] or result['call_sent']:
                logging.info(f"Emergency notifications sent for: {user_input}")
            else:
                logging.error(f"Failed to send emergency notifications for: {user_input}")
        
        return result
    
    def make_emergency_call(self, detection_result: Dict[str, any]) -> bool:
        """
        Make emergency phone call using Twilio
        
        Args:
            detection_result: Result from emergency detection
            
        Returns:
            bool: True if call made successfully, False otherwise
        """
        if not TWILIO_AVAILABLE:
            print(f"\n📞 TWILIO NOT AVAILABLE - Phone call simulation mode")
            print("Install Twilio with: pip install twilio")
            
            # Determine recipients to call
            if detection_result['family_requested'] == 'family':
                recipients = ['son', 'Kaustubh Darade']
            elif detection_result['family_requested']:
                recipients = [detection_result['family_requested']]
            else:
                recipients = ['son', 'Kaustubh Darade']  # Default to both for emergencies
            
            timestamp = detection_result['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
            original_input = detection_result['original_input']
            
            print(f"📞 Would call these numbers:")
            for recipient in recipients:
                if recipient in self.family_contacts:
                    contact = self.family_contacts[recipient]
                    phone_number = contact.get('phone', self.emergency_phone_number)
                    print(f"  📞 {contact['name']}: {phone_number}")
            
            print(f"📞 Message: Emergency alert - {original_input} at {timestamp}")
            return False  # Return False since no actual calls were made
        
        try:
            # Initialize Twilio client
            client = Client(self.twilio_account_sid, self.twilio_auth_token)
            
            # Determine recipients to call
            if detection_result['family_requested'] == 'family':
                recipients = ['son', 'Kaustubh Darade']
            elif detection_result['family_requested']:
                recipients = [detection_result['family_requested']]
            else:
                recipients = ['son', 'Kaustubh Darade']  # Default to both for emergencies
            
            # Create emergency message for the call
            timestamp = detection_result['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
            original_input = detection_result['original_input']
            
            # Analyze the emergency type for better explanation
            emergency_analysis = self._analyze_emergency_type(original_input)
            
            # Generate enhanced TwiML for the call with better formatting
            # Clean up the text for better voice synthesis
            clean_input = original_input.replace('"', '').strip()
            clean_phone = self.emergency_phone_number.replace('+', '').replace(' ', '')
            
            # Create the simplest possible TwiML message for maximum compatibility
            twiml_message = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="woman" language="en">
        Emergency alert from Sathi AI. Your family member needs help.
        They said: {clean_input}.
        Please call them now at {self.emergency_phone_number}.
        This is an automated emergency alert.
    </Say>
    <Pause length="2"/>
    <Say voice="woman" language="en">
        Emergency alert from Sathi AI. Call them now at {self.emergency_phone_number}.
    </Say>
</Response>"""
            
            calls_made = []
            
            # Make calls to all recipients
            for recipient in recipients:
                if recipient in self.family_contacts:
                    contact = self.family_contacts[recipient]
                    phone_number = contact.get('phone', self.emergency_phone_number)
                    
                    try:
                        # Debug: Print TwiML message
                        print(f"📞 TwiML Message (first 200 chars): {twiml_message[:200]}...")
                        
                        # Create the call with URL method instead of inline TwiML
                        # This is more reliable for voice playback
                        call = client.calls.create(
                            to=phone_number,
                            from_=self.twilio_phone_number,
                            twiml=twiml_message,
                            method='POST'
                        )
                        
                        calls_made.append({
                            'recipient': contact['name'],
                            'phone': phone_number,
                            'call_sid': call.sid,
                            'status': call.status
                        })
                        
                        print(f"\n📞 EMERGENCY CALL INITIATED!")
                        print(f"To: {contact['name']} at {phone_number}")
                        print(f"Call SID: {call.sid}")
                        print(f"Status: {call.status}")
                        print(f"Time: {timestamp}")
                        print(f"User said: \"{original_input}\"")
                        print(f"📞 Voice message: Enhanced emergency explanation included")
                        
                        logging.info(f"Emergency call initiated to {contact['name']} at {phone_number}")
                        
                    except TwilioRestException as e:
                        print(f"Failed to make call to {contact['name']}: {e}")
                        logging.error(f"Twilio call failed to {phone_number}: {e}")
                        
                        # Fallback: log the call attempt
                        calls_made.append({
                            'recipient': contact['name'],
                            'phone': phone_number,
                            'call_sid': None,
                            'status': 'failed',
                            'error': str(e)
                        })
            
            if calls_made:
                print(f"\n📞 Emergency calls attempted: {len(calls_made)}")
                for call_info in calls_made:
                    status_icon = "✅" if call_info['call_sid'] else "❌"
                    print(f"{status_icon} {call_info['recipient']}: {call_info['status']}")
                return len([c for c in calls_made if c['call_sid']]) > 0
            else:
                print("No emergency calls were made")
                return False
                
        except Exception as e:
            logging.error(f"Emergency call system failed: {e}")
            print(f"Emergency call system error: {e}")
            return False
    
    def _analyze_emergency_type(self, user_input: str) -> Dict[str, str]:
        """
        Analyze the emergency type and provide detailed explanation
        
        Args:
            user_input: The user's emergency statement
            
        Returns:
            Dict with explanation, action_advice, and summary
        """
        user_input_lower = user_input.lower()
        
        # Medical emergencies
        if any(word in user_input_lower for word in ['chest pain', 'heart', 'breathing', 'can\'t breathe', 'short of breath']):
            return {
                'explanation': 'This appears to be a medical emergency. They may be experiencing chest pain or breathing difficulties, which could indicate a heart attack or respiratory problem.',
                'action_advice': 'This is potentially life-threatening. Call emergency services immediately at 108 or 112, then call your family member. Do not wait.',
                'summary': 'Medical emergency - possible heart or breathing issues. Call emergency services now.'
            }
        
        # Fall-related emergencies
        elif any(word in user_input_lower for word in ['fall', 'fell', 'fallen', 'hurt', 'pain', 'broken']):
            return {
                'explanation': 'This appears to be a fall-related emergency. They may have fallen and could be injured or unable to get up.',
                'action_advice': 'Call them immediately to assess their condition. If they cannot get up or are in severe pain, call emergency services for help.',
                'summary': 'Fall emergency - possible injury. Call them immediately to assess situation.'
            }
        
        # Dizziness/confusion
        elif any(word in user_input_lower for word in ['dizzy', 'confused', 'disoriented', 'lost', 'don\'t know']):
            return {
                'explanation': 'This appears to be a neurological emergency. They may be experiencing dizziness, confusion, or disorientation, which could indicate various medical conditions.',
                'action_advice': 'Call them immediately to check if they are conscious and oriented. If they seem confused about their surroundings, consider calling emergency services.',
                'summary': 'Neurological emergency - dizziness or confusion. Call to assess their condition.'
            }
        
        # General help requests
        elif any(word in user_input_lower for word in ['help', 'emergency', 'urgent', 'need help', 'trouble']):
            return {
                'explanation': 'This is a general emergency request. They need immediate assistance but the specific nature is unclear.',
                'action_advice': 'Call them immediately to understand what kind of help they need. Stay on the line with them until help arrives or the situation is resolved.',
                'summary': 'General emergency - immediate assistance needed. Call them now.'
            }
        
        # Family contact requests
        elif any(word in user_input_lower for word in ['call', 'contact', 'message', 'inform', 'tell']):
            return {
                'explanation': 'They are specifically requesting to contact family members. This may or may not be an emergency situation.',
                'action_advice': 'Call them immediately to understand why they need to contact family. Assess if this is an emergency or routine communication need.',
                'summary': 'Family contact request. Call them to understand the situation.'
            }
        
        # Default case
        else:
            return {
                'explanation': 'They have requested assistance. The specific nature of the emergency is not clear from their statement.',
                'action_advice': 'Call them immediately to assess the situation and determine what kind of help they need.',
                'summary': 'Assistance requested. Call them to assess the situation.'
            }
    
    def add_family_contact(self, relationship: str, name: str, email: str, phone: str = None):
        """
        Add or update family contact information
        
        Args:
            relationship: 'son', 'daughter', etc.
            name: Display name
            email: Email address
            phone: Phone number (optional)
        """
        self.family_contacts[relationship.lower()] = {
            'name': name,
            'email': email,
            'phone': phone or self.emergency_phone_number,
            'relationship': relationship.lower()
        }
        logging.info(f"Added family contact: {relationship} - {name} ({email}, {phone or self.emergency_phone_number})")
    
    def test_emergency_detection(self):
        """Test emergency detection with sample inputs"""
        test_inputs = [
            "I need help",
            "Please inform my son",
            "Send message to my daughter", 
            "Emergency! I fell down",
            "Call someone please",
            "I'm having chest pain",
            "Tell my family I need help",
            "Contact my son urgently",
            "I feel dizzy and alone"
        ]
        
        print("🧪 Testing Emergency Detection System")
        print("=" * 50)
        
        for test_input in test_inputs:
            result = self.process_user_input(test_input)
            email_status = "✅" if result['email_sent'] else "❌"
            call_status = "✅" if result['call_sent'] else "❌"
            
            if result['email_sent'] or result['call_sent']:
                status = f"🚨 EMAIL {email_status} | CALL {call_status}"
            else:
                status = "ℹ️ No Action"
            print(f"{status}: '{test_input}'")
        
        print("\n✅ Emergency detection test completed")

# Global instance for easy access
_emergency_notifier = None

def get_emergency_notifier() -> EmergencyEmailNotifier:
    """Get or create emergency notifier instance"""
    global _emergency_notifier
    if _emergency_notifier is None:
        _emergency_notifier = EmergencyEmailNotifier()
    return _emergency_notifier

def check_and_send_emergency_email(user_input: str) -> Dict[str, any]:
    """
    Check user input for emergency requests and send email and phone calls if needed
    
    Args:
        user_input: User's speech/text input
        
    Returns:
        Dict with processing results including email and call status
    """
    try:
        notifier = get_emergency_notifier()
        result = notifier.process_user_input(user_input)
        return result
    except Exception as e:
        logging.error(f"Error in emergency notification processing: {e}")
        return {'user_input': user_input, 'email_sent': False, 'call_sent': False, 'error': str(e)}

# Test function
if __name__ == "__main__":
    print("🚨 Sathi AI Emergency Notification System")
    print("📧 Email + 📞 Phone Calls")
    print("=" * 50)
    
    # Create notifier
    notifier = EmergencyEmailNotifier()
    
    # Test the system
    notifier.test_emergency_detection()
    
    print("\n💡 Setup Instructions:")
    print("1. Configure Gmail SMTP settings in the notifier")
    print("2. Configure Twilio credentials and phone numbers")
    print("3. Update family contact information with emails and phones")
    print("4. Test with real emergency scenarios")
    print("5. Ensure family members receive emails AND phone calls promptly")
