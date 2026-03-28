"""
Advanced Emergency Handling System for Sathi AI Voice Assistant
Provides reliable, human-like emergency detection and response with fail-safe mechanisms
"""

import sys
from pathlib import Path

# Add project root to sys.path for absolute imports
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import threading
import time
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, Callable
from enum import Enum
import queue
import re

# Import existing components
from core.voice_input import record_audio, transcribe_audio, ELDERLY_AUDIO_CONFIG
from core.tts_output import speak_text
from core.emergency_email import EmergencyEmailNotifier


class EmergencyLevel(Enum):
    """Emergency alert levels"""
    FIRST_ALERT = "first_alert"
    SECOND_ALERT = "second_alert"
    CONFIRMED_EMERGENCY = "confirmed_emergency"


class EmergencyStatus(Enum):
    """Emergency response status"""
    DETECTED = "detected"
    WAITING_CONFIRMATION = "waiting_confirmation"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    NO_RESPONSE = "no_response"


class EmergencyHandler:
    """Advanced emergency detection and response system"""
    
    def __init__(self, log_file: str = "data/emergency_log.json"):
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(exist_ok=True)
        
        # Emergency detection patterns
        self.emergency_keywords = [
            "help", "emergency", "i fell", "i am alone", "i need help", 
            "i am not feeling well", "not feeling well", "chest pain", 
            "can't breathe", "dizzy", "hurt", "hurts", "hurting", "sick", "trouble", "fall",
            "fell down", "unwell", "urgent", "call someone", "contact family",
            "call my son", "call my daughter", "contact my son", "contact my daughter",
            "pain", "ache", "sore", "uncomfortable"
        ]
        
        # Negative confirmation patterns (to cancel emergency)
        self.cancel_patterns = [
            "no", "i'm fine", "i am fine", "i'm okay", "i am okay", 
            "fine", "okay", "ok", "no help", "not needed", "nothing wrong",
            "all good", "good", "better now"
        ]
        
        # Positive confirmation patterns
        self.confirm_patterns = [
            "yes", "help", "need help", "call", "contact", "emergency", 
            "not okay", "not fine", "sick", "pain", "hurt", "fell"
        ]
        
        # Email notifier
        self.email_notifier = EmergencyEmailNotifier()
        
        # Thread safety
        self._emergency_lock = threading.Lock()
        self._response_queue = queue.Queue()
        self._stop_listening = threading.Event()
        
        # Logging
        self._setup_logging()
        
        logging.info("Emergency Handler initialized")
    
    def _setup_logging(self):
        """Setup emergency-specific logging"""
        self.logger = logging.getLogger("emergency_handler")
        self.logger.setLevel(logging.INFO)
        
        # File handler for emergency logs
        handler = logging.FileHandler(self.log_file.with_suffix('.log'))
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
    
    def detect_emergency(self, text: str) -> Tuple[bool, float]:
        """
        Detect emergency in user input using keyword matching and intent analysis
        
        Args:
            text: User input text
            
        Returns:
            Tuple of (emergency_detected, confidence_score)
        """
        if not text:
            return False, 0.0
        
        text_lower = text.lower().strip()
        
        # Keyword matching - check for exact words and phrases
        keyword_matches = 0
        for keyword in self.emergency_keywords:
            if keyword in text_lower:
                keyword_matches += 1
                # Give extra weight for exact matches
                if len(keyword.split()) > 1:  # Multi-word phrases
                    keyword_matches += 1
        
        keyword_score = min(keyword_matches / len(self.emergency_keywords), 1.0)
        
        # Intent-based detection using patterns
        emergency_patterns = [
            r'(i\s+)?(need\s+)?help\s+(me|now|urgent)',
            r'(i\s+)?(am\s+)?(not\s+)?feeling\s+(well|good)',
            r'(i\s+)?(have\s+)?(chest\s+)?pain',
            r'(can\'t|cannot)\s+breathe',
            r'(i\s+)?(fell|fall)\s+(down|over)',
            r'(call|contact)\s+(someone|family|son|daughter)',
            r'(i\s+)?am\s+alone',
            r'(urgent|emergency|trouble)',
            r'(i\s+)?(have\s+)?(a\s+)?(head|stomach|back)\s+ache',
            r'(my\s+)?(head|stomach|back|chest)\s+hurts?',
            r'(i\'m|i\s+am)\s+(in\s+)?(pain|hurting)',
            r'(it\s+)?(is\s+)?(it\'s\s+)?hurting',
            r'(i\s+)?(feel\s+)?(uncomfortable|sore|dizzy)'
        ]
        
        pattern_matches = sum(1 for pattern in emergency_patterns 
                            if re.search(pattern, text_lower))
        pattern_score = min(pattern_matches / len(emergency_patterns), 1.0)
        
        # Combined confidence score
        confidence = (keyword_score * 0.6 + pattern_score * 0.4)
        
        emergency_detected = confidence > 0.05  # Lower threshold for better detection
        
        self.logger.info(f"Emergency detection: '{text}' -> {emergency_detected} (confidence: {confidence:.2f})")
        
        return emergency_detected, confidence
    
    def _analyze_response(self, text: str) -> str:
        """
        Analyze user response to determine if emergency should be confirmed or cancelled
        
        Args:
            text: User response text
            
        Returns:
            'confirm', 'cancel', or 'unclear'
        """
        if not text:
            return 'unclear'
        
        text_lower = text.lower().strip()
        
        # Check for cancellation patterns
        for cancel_pattern in self.cancel_patterns:
            if cancel_pattern in text_lower:
                return 'cancel'
        
        # Check for confirmation patterns
        for confirm_pattern in self.confirm_patterns:
            if confirm_pattern in text_lower:
                return 'confirm'
        
        return 'unclear'
    
    def wait_for_response(self, timeout: int = 15) -> Tuple[str, Optional[str]]:
        """
        Wait for user response during emergency confirmation
        
        Args:
            timeout: Timeout in seconds
            
        Returns:
            Tuple of (response_type, transcribed_text)
        """
        self.logger.info(f"Waiting for user response (timeout: {timeout}s)")
        
        response_received = threading.Event()
        response_result = {'type': 'no_response', 'text': None}
        
        def _listen_for_response():
            """Background thread to listen for response"""
            try:
                # Record audio with timeout
                audio_path = record_audio(
                    duration=timeout,
                    filename=None,
                    use_vad=True
                )
                
                if audio_path and not self._stop_listening.is_set():
                    # Transcribe the response
                    transcription = transcribe_audio(audio_path, delete_after=True)
                    
                    if transcription:
                        response_type = self._analyze_response(transcription)
                        response_result['type'] = response_type
                        response_result['text'] = transcription
                        self.logger.info(f"User response: '{transcription}' -> {response_type}")
                    
                response_received.set()
                
            except Exception as e:
                self.logger.error(f"Error listening for response: {e}")
                response_result['type'] = 'error'
                response_result['text'] = str(e)
                response_received.set()
        
        # Start listening thread
        listen_thread = threading.Thread(target=_listen_for_response, daemon=True)
        listen_thread.start()
        
        # Wait for response or timeout
        response_received.wait(timeout=timeout)
        
        # Stop listening if still running
        self._stop_listening.set()
        
        return response_result['type'], response_result['text']
    
    def send_alert_email(self, level: EmergencyLevel, user_input: str, 
                        status: EmergencyStatus, timestamp: datetime) -> bool:
        """
        Send emergency alert email with appropriate level and content
        
        Args:
            level: Emergency alert level
            user_input: Original user input that triggered emergency
            status: Current emergency status
            timestamp: When emergency was detected
            
        Returns:
            True if email sent successfully
        """
        try:
            # Create custom message based on level
            if level == EmergencyLevel.FIRST_ALERT:
                custom_message = """Possible emergency detected from Sathi AI.

No response received from user after initial check.

ACTION REQUIRED:
Please call immediately to check on their safety and wellbeing."""
            
            elif level == EmergencyLevel.SECOND_ALERT:
                custom_message = """CRITICAL: No response from user after multiple attempts.

User has not responded to multiple emergency confirmation attempts.

IMMEDIATE ACTION REQUIRED:
This may be a real emergency. Call immediately and if no response, 
consider contacting emergency services or visiting in person."""
            
            else:  # CONFIRMED_EMERGENCY
                custom_message = """CONFIRMED EMERGENCY from Sathi AI.

User has confirmed they need emergency help.

IMMEDIATE ACTION REQUIRED:
This is a confirmed emergency. Call immediately and provide assistance.
Consider emergency services if the situation warrants."""
            
            # Create detection result for custom email
            detection_result = {
                'emergency_detected': True,
                'family_requested': None,
                'original_input': user_input,
                'timestamp': timestamp,
                'should_notify': True,
                'emergency_level': level.value,
                'emergency_status': status.value,
                'custom_message': custom_message
            }
            
            # Log the alert
            self.logger.info(f"Sending {level.value} email")
            
            # Use email notifier with custom content
            success = self.email_notifier.send_emergency_email(detection_result)
            
            if success:
                self._log_emergency_event(user_input, level, status, timestamp, "email_sent")
            else:
                self._log_emergency_event(user_input, level, status, timestamp, "email_failed")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error sending alert email: {e}")
            self._log_emergency_event(user_input, level, status, timestamp, f"email_error: {e}")
            return False
    
    def _log_emergency_event(self, user_input: str, level: EmergencyLevel, 
                           status: EmergencyStatus, timestamp: datetime, 
                           event_type: str):
        """Log emergency event to JSON file for KPI tracking"""
        try:
            log_entry = {
                'timestamp': timestamp.isoformat(),
                'user_input': user_input,
                'emergency_level': level.value,
                'emergency_status': status.value,
                'event_type': event_type
            }
            
            # Read existing logs
            logs = []
            if self.log_file.exists():
                try:
                    with open(self.log_file, 'r', encoding='utf-8') as f:
                        logs = json.load(f)
                except (json.JSONDecodeError, FileNotFoundError):
                    logs = []
            
            # Add new entry
            logs.append(log_entry)
            
            # Keep only last 100 entries to prevent file from growing too large
            if len(logs) > 100:
                logs = logs[-100:]
            
            # Write back
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump(logs, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"Error logging emergency event: {e}")
    
    def handle_emergency(self, user_input: str) -> bool:
        """
        Handle emergency detection and response flow with human-like conversation
        
        Args:
            user_input: User input that triggered emergency detection
            
        Returns:
            True if emergency was handled (regardless of outcome)
        """
        emergency_timestamp = datetime.now()
        
        try:
            with self._emergency_lock:
                self.logger.info(f"Starting emergency handling for: '{user_input}'")
                self._log_emergency_event(user_input, EmergencyLevel.FIRST_ALERT, 
                                        EmergencyStatus.DETECTED, emergency_timestamp, "emergency_detected")
                
                # Step 1: Immediate, short, caring response about pain
                pain_keywords = ['pain', 'hurting', 'hurt', 'ache', 'sore', 'uncomfortable']
                has_pain = any(word in user_input.lower() for word in pain_keywords)
                
                if has_pain:
                    first_response = "Oh no! Where are you hurting? Tell me what's wrong."
                else:
                    first_response = "I'm here with you. What's happening? Are you okay?"
                
                speak_text(first_response)
                print(f"Sathi: {first_response}")
                
                # Step 2: Wait for first response (15 seconds)
                self._stop_listening.clear()
                response_type, response_text = self.wait_for_response(timeout=15)
                
                if response_type == 'cancel':
                    # User cancelled emergency
                    cancel_msg = "Okay, I'm glad you're alright. I'm here if you need anything."
                    speak_text(cancel_msg)
                    print(f"Sathi: {cancel_msg}")
                    
                    self._log_emergency_event(user_input, EmergencyLevel.FIRST_ALERT, 
                                            EmergencyStatus.CANCELLED, emergency_timestamp, "user_cancelled")
                    return True
                
                elif response_type == 'confirm' or (response_text and response_text.strip()):
                    # User responded - provide comfort and ask if they need help
                    if has_pain:
                        comfort_response = "I understand you're in pain. Should I call your family to help you?"
                    else:
                        comfort_response = "I hear you. Do you need me to contact your family for help?"
                    
                    speak_text(comfort_response)
                    print(f"Sathi: {comfort_response}")
                    
                    # Wait for confirmation about calling family
                    self._stop_listening.clear()
                    confirm_response, confirm_text = self.wait_for_response(timeout=10)
                    
                    if confirm_response == 'confirm' or (confirm_text and any(word in confirm_text.lower() for word in ['yes', 'call', 'help', 'please'])):
                        # User wants help - send immediate alert
                        self.send_alert_email(EmergencyLevel.CONFIRMED_EMERGENCY, user_input,
                                            EmergencyStatus.CONFIRMED, emergency_timestamp)
                        
                        confirm_msg = "I'm calling your family right now. They'll help you."
                        speak_text(confirm_msg)
                        print(f"Sathi: {confirm_msg}")
                        
                        self._log_emergency_event(user_input, EmergencyLevel.CONFIRMED_EMERGENCY, 
                                                EmergencyStatus.CONFIRMED, emergency_timestamp, "user_confirmed")
                        return True
                    else:
                        # User doesn't want help
                        no_help_msg = "Okay, I'll stay here with you. Let me know if you need anything."
                        speak_text(no_help_msg)
                        print(f"Sathi: {no_help_msg}")
                        
                        self._log_emergency_event(user_input, EmergencyLevel.FIRST_ALERT, 
                                                EmergencyStatus.CANCELLED, emergency_timestamp, "user_declined_help")
                        return True
                
                else:
                    # No response - ask again more urgently
                    if has_pain:
                        second_check = "I didn't hear you. Are you in pain? Should I call someone?"
                    else:
                        second_check = "I didn't hear you. Are you okay? Do you need help?"
                    
                    speak_text(second_check)
                    print(f"Sathi: {second_check}")
                    
                    # Step 4: Wait for second response (10 seconds - shorter for urgency)
                    self._stop_listening.clear()
                    response_type2, response_text2 = self.wait_for_response(timeout=10)
                    
                    if response_type2 == 'cancel':
                        # User cancelled on second check
                        cancel_msg = "Okay, good to hear you're alright. I'm here if you need me."
                        speak_text(cancel_msg)
                        print(f"Sathi: {cancel_msg}")
                        
                        self._log_emergency_event(user_input, EmergencyLevel.FIRST_ALERT, 
                                                EmergencyStatus.CANCELLED, emergency_timestamp, "user_cancelled_second")
                        return True
                    
                    elif response_type2 == 'confirm' or (response_text2 and response_text2.strip()):
                        # User responded on second check - send alert
                        self.send_alert_email(EmergencyLevel.CONFIRMED_EMERGENCY, user_input,
                                            EmergencyStatus.CONFIRMED, emergency_timestamp)
                        
                        confirm_msg = "I'm calling your family now. Help is coming."
                        speak_text(confirm_msg)
                        print(f"Sathi: {confirm_msg}")
                        
                        self._log_emergency_event(user_input, EmergencyLevel.CONFIRMED_EMERGENCY, 
                                                EmergencyStatus.CONFIRMED, emergency_timestamp, "user_confirmed_second")
                        return True
                    
                    else:
                        # Still no response - send urgent alert
                        self.send_alert_email(EmergencyLevel.SECOND_ALERT, user_input,
                                            EmergencyStatus.NO_RESPONSE, emergency_timestamp)
                        
                        final_msg = "I'm calling your family right now. They'll help you. I'm staying with you."
                        speak_text(final_msg)
                        print(f"Sathi: {final_msg}")
                        
                        self._log_emergency_event(user_input, EmergencyLevel.SECOND_ALERT, 
                                                EmergencyStatus.NO_RESPONSE, emergency_timestamp, "no_response_final")
                        return True
                
        except Exception as e:
            self.logger.error(f"Error in emergency handling: {e}")
            self._log_emergency_event(user_input, EmergencyLevel.FIRST_ALERT, 
                                    EmergencyStatus.DETECTED, emergency_timestamp, f"handling_error: {e}")
            
            # Fail-safe response
            error_msg = "I'm having trouble but I'm here to help. Let me contact your family for you."
            speak_text(error_msg)
            print(f"Sathi: {error_msg}")
            
            # Send emergency alert anyway as fail-safe
            try:
                self.send_alert_email(EmergencyLevel.SECOND_ALERT, user_input,
                                    EmergencyStatus.DETECTED, emergency_timestamp)
            except:
                pass  # Already logged above
            
            return True


# Global instance for easy access
_emergency_handler = None

def get_emergency_handler() -> EmergencyHandler:
    """Get or create emergency handler instance"""
    global _emergency_handler
    if _emergency_handler is None:
        _emergency_handler = EmergencyHandler()
    return _emergency_handler

def check_and_handle_emergency(user_input: str) -> bool:
    """
    Check user input for emergency and handle if detected
    
    Args:
        user_input: User's speech/text input
        
    Returns:
        True if emergency was detected and handled
    """
    try:
        handler = get_emergency_handler()
        emergency_detected, confidence = handler.detect_emergency(user_input)
        
        if emergency_detected:
            logging.info(f"Emergency detected with confidence {confidence:.2f}: '{user_input}'")
            return handler.handle_emergency(user_input)
        
        return False
        
    except Exception as e:
        logging.error(f"Error in emergency check and handle: {e}")
        return False

# Test function
if __name__ == "__main__":
    print("🚨 Advanced Emergency Handler Test")
    print("=" * 50)
    
    handler = EmergencyHandler()
    
    # Test emergency detection
    test_phrases = [
        "help me please",
        "i fell down",
        "i am alone",
        "i'm not feeling well",
        "chest pain",
        "i need help now",
        "call my son"
    ]
    
    print("Testing emergency detection:")
    for phrase in test_phrases:
        detected, confidence = handler.detect_emergency(phrase)
        status = "🚨 DETECTED" if detected else "ℹ️ Normal"
        print(f"{status}: '{phrase}' (confidence: {confidence:.2f})")
    
    print("\n✅ Emergency handler test completed")
