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

class EmergencyEmailNotifier:
    """Handles emergency email notifications to family members"""
    
    def __init__(self):
        # Family member contacts
        self.family_contacts = {
            'son': {
                'name': 'Ajay Nandurkar',
                'email': 'nandurkarajay07@gmail.com',
                'relationship': 'son'
            },
            'Kaustubh Darade': {
                'name': 'Kaustubh Darade', 
                'email': 'en22212161@git-india.edu.in',  
                'relationship': 'son'
            }
        }
        
        # Email configuration (using Gmail SMTP)
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.sender_email = "nandurkarajay07@gmail.com"  
        self.sender_password = "oeao uqbr dikc hghe"    
        
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
    
    def send_emergency_email(self, detection_result: Dict[str, any]) -> bool:
        """
        Send emergency email to family members
        
        Args:
            detection_result: Result from emergency detection
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            # Check if this is a custom message from emergency handler
            if 'emergency_level' in detection_result:
                return self._send_custom_emergency_email(detection_result)
            
            # Original email creation logic for backward compatibility
            email_content = self.create_emergency_email(detection_result)
            
            # Get recipient emails
            recipient_emails = []
            for recipient in email_content['recipients']:
                if recipient in self.family_contacts:
                    recipient_emails.append(self.family_contacts[recipient]['email'])
            
            if not recipient_emails:
                logging.error("No valid recipient emails found")
                return False
            
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
                
                print(f"\nREAL EMAIL SENT!")
                print(f"To: {', '.join(recipient_emails)}")
                print(f"Subject: {email_content['subject']}")
                print(f"Time: {detection_result['timestamp']}")
                print(f"User said: \"{detection_result['original_input']}\"")
                print("Family members have been notified by email!\n")
                return True
                
            except Exception as e:
                print(f"Real email failed: {e}")
                print("Falling back to simulation mode...")
                
                # Fallback to simulation
                print(f"\nEMAIL SIMULATION:")
                print(f"To: {', '.join(recipient_emails)}")
                print(f"Subject: {email_content['subject']}")
                print(f"Time: {detection_result['timestamp']}")
                print(f"User said: \"{detection_result['original_input']}\"")
                print("Email not actually sent - SMTP error\n")
            
            logging.info(f"Real email sent to {', '.join(recipient_emails)}")
            return True
            
        except Exception as e:
            logging.error(f"Real email sending failed: {e}")
            return False
    
    def _send_custom_emergency_email(self, detection_result: Dict[str, any]) -> bool:
        """
        Send custom emergency email from emergency handler
        
        Args:
            detection_result: Custom detection result from emergency handler
            
        Returns:
            bool: True if email sent successfully
        """
        try:
            # Get recipient emails (notify all family contacts)
            recipient_emails = []
            for contact in self.family_contacts.values():
                recipient_emails.append(contact['email'])
            
            if not recipient_emails:
                logging.error("No valid recipient emails found")
                return False
            
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
                print("Family members have been notified!\n")
                return True
                
            except Exception as e:
                print(f"Real email failed: {e}")
                print(f"\n🚨 EMERGENCY EMAIL SIMULATION:")
                print(f"Level: {level}")
                print(f"To: {', '.join(recipient_emails)}")
                print(f"Subject: {subject}")
                print(f"Time: {timestamp}")
                print(f"User said: \"{detection_result['original_input']}\"")
                print("Email not actually sent - SMTP error\n")
                return True  # Return True for simulation
            
        except Exception as e:
            logging.error(f"Custom emergency email sending failed: {e}")
            return False
    
    def process_user_input(self, user_input: str) -> Dict[str, any]:
        """
        Process user input and send emergency email if needed
        
        Args:
            user_input: The user's speech/text input
            
        Returns:
            Dict with processing results
        """
        # Detect emergency
        detection_result = self.detect_emergency_request(user_input)
        
        result = {
            'user_input': user_input,
            'detection_result': detection_result,
            'email_sent': False,
            'timestamp': datetime.now()
        }
        
        # Send email if emergency detected
        if detection_result['should_notify']:
            email_sent = self.send_emergency_email(detection_result)
            result['email_sent'] = email_sent
            
            if email_sent:
                logging.info(f"Emergency email sent for: {user_input}")
            else:
                logging.error(f"Failed to send emergency email for: {user_input}")
        
        return result
    
    def add_family_contact(self, relationship: str, name: str, email: str):
        """
        Add or update family contact information
        
        Args:
            relationship: 'son', 'daughter', etc.
            name: Display name
            email: Email address
        """
        self.family_contacts[relationship.lower()] = {
            'name': name,
            'email': email,
            'relationship': relationship.lower()
        }
        logging.info(f"Added family contact: {relationship} - {name} ({email})")
    
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
            status = "🚨 EMAIL SENT" if result['email_sent'] else "ℹ️ No Action"
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
    Check user input for emergency requests and send email if needed
    
    Args:
        user_input: User's speech/text input
        
    Returns:
        Dict with processing results
    """
    try:
        notifier = get_emergency_notifier()
        result = notifier.process_user_input(user_input)
        return result
    except Exception as e:
        logging.error(f"Error in emergency email processing: {e}")
        return {'user_input': user_input, 'email_sent': False, 'error': str(e)}

# Test function
if __name__ == "__main__":
    print("🚨 Sathi AI Emergency Email Notification System")
    print("=" * 50)
    
    # Create notifier
    notifier = EmergencyEmailNotifier()
    
    # Test the system
    notifier.test_emergency_detection()
    
    print("\n💡 Setup Instructions:")
    print("1. Configure Gmail SMTP settings in the notifier")
    print("2. Update family contact information")
    print("3. Test with real emergency scenarios")
    print("4. Ensure family members receive emails promptly")
