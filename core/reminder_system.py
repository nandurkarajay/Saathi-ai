"""
Reminder System for Sathi AI
Combines reminder management, natural language parsing, and sound alerts
"""

import sqlite3
import re
import logging
import winsound
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass

@dataclass
class ReminderResponse:
    """Container for reminder processing results"""
    spoken_text: str
    display_text: str
    reminder_data: Optional[Dict[str, Any]] = None

# Configure logging
PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOG_PATH = PROJECT_ROOT / 'data' / 'reminder_system.log'
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename=str(LOG_PATH),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Database path - sathi.db
DB_PATH = PROJECT_ROOT / 'sathi.db'

# =============================================================================
# Ring Sound Module
# =============================================================================

class RingSound:
    """Handles ring/alert sounds for reminders"""
    
    # Windows system sounds
    SOUNDS = {
        'alarm': winsound.SND_ALIAS,  # System alarm
        'reminder': winsound.MB_ICONASTERISK,  # Gentle reminder
        'urgent': winsound.MB_ICONEXCLAMATION,  # Urgent alert
    }
    
    # Frequencies for beep sounds (Hz)
    FREQUENCIES = {
        'low': 400,
        'medium': 800,
        'high': 1200,
    }
    
    @staticmethod
    def play_system_sound(sound_type: str = 'reminder') -> bool:
        """Play a Windows system sound"""
        try:
            if sound_type == 'alarm':
                winsound.MessageBeep(winsound.MB_ICONHAND)
                logging.info("🔔 Played alarm sound")
            elif sound_type == 'reminder':
                winsound.MessageBeep(winsound.MB_ICONASTERISK)
                logging.info("🔔 Played reminder sound")
            elif sound_type == 'urgent':
                winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
                logging.info("🔔 Played urgent sound")
            else:
                winsound.MessageBeep()
                logging.info("🔔 Played default beep")
            return True
        except Exception as e:
            logging.error(f"❌ Error playing system sound: {e}")
            return False
    
    @staticmethod
    def play_beep_sequence(pattern: str = 'gentle') -> bool:
        """Play a sequence of beeps"""
        try:
            if pattern == 'gentle':
                winsound.Beep(800, 300)
                time.sleep(0.2)
                winsound.Beep(800, 300)
                logging.info("🔔 Played gentle beep sequence")
            elif pattern == 'alert':
                for _ in range(3):
                    winsound.Beep(1000, 400)
                    time.sleep(0.3)
                logging.info("🔔 Played alert beep sequence")
            elif pattern == 'urgent':
                for _ in range(5):
                    winsound.Beep(1200, 200)
                    time.sleep(0.1)
                logging.info("🔔 Played urgent beep sequence")
            elif pattern == 'wake':
                for freq in [600, 800, 1000, 1200]:
                    winsound.Beep(freq, 500)
                    time.sleep(0.1)
                logging.info("🔔 Played wake-up sequence")
            return True
        except Exception as e:
            logging.error(f"❌ Error playing beep sequence: {e}")
            return False
    
    @staticmethod
    def play_reminder_alert(elderly_friendly: bool = True) -> bool:
        """Play an elderly-friendly reminder alert"""
        try:
            if elderly_friendly:
                winsound.Beep(700, 400)
                time.sleep(0.5)
                winsound.Beep(700, 400)
                time.sleep(0.3)
                winsound.Beep(700, 400)
                logging.info("🔔 Played elderly-friendly reminder alert")
            else:
                winsound.MessageBeep(winsound.MB_ICONASTERISK)
                logging.info("🔔 Played standard reminder alert")
            return True
        except Exception as e:
            logging.error(f"❌ Error playing reminder alert: {e}")
            return False
    
    @staticmethod
    def play_custom_wav(wav_path: str) -> bool:
        """Play a custom WAV file"""
        try:
            wav_file = Path(wav_path)
            if not wav_file.exists():
                logging.error(f"❌ WAV file not found: {wav_path}")
                return False
            winsound.PlaySound(str(wav_file), winsound.SND_FILENAME)
            logging.info(f"🔔 Played custom WAV: {wav_path}")
            return True
        except Exception as e:
            logging.error(f"❌ Error playing WAV file: {e}")
            return False

# Convenience functions
def ring_for_reminder(gentle: bool = True) -> bool:
    """Play ring sound for a reminder"""
    return RingSound.play_reminder_alert(elderly_friendly=gentle)

def ring_for_alarm() -> bool:
    """Play ring sound for an alarm (wake-up)"""
    return RingSound.play_beep_sequence(pattern='wake')

def ring_urgent() -> bool:
    """Play urgent alert sound"""
    return RingSound.play_beep_sequence(pattern='urgent')

# =============================================================================
# Reminder Parser Module
# =============================================================================

class ReminderParser:
    """Parse natural language reminders into structured data"""
    
    # Reminder/Alarm trigger patterns
    REMINDER_PATTERNS = [
        r'(?:set|create|make|add).*?(?:reminder|alarm)',
        r'(?:a|an)\s+(?:reminder|alarm)\s+(?:for|at)',
        r'reminder\s+(?:for|at)',
        r'alarm\s+(?:for|at)',
        r'remind me',
        r'wake me up',
        r'alert me',
        r'notify me',
        r'don\'t forget',
        r'remember to remind me',
        r'alarm\s+.+',  # Catch any "alarm" followed by something
        r'reminder\s+.+',  # Catch any "reminder" followed by something
    ]
    
    # Time extraction patterns
    TIME_PATTERNS = [
        # Military time patterns (elderly-friendly)
        (r'(\d{1,2})\s+hundred\s+hours?', 'military'),  # "19 hundred hours"
        (r'(\d{1,2})\s+hundred', 'military_simple'),  # "19 hundred"
        (r'(\d{1,2})\s*hours?', 'hours_format'),  # "19 hours"
        # 24-hour format patterns
        (r'(\d{1,2}):(\d{2})\s*(am|pm|a\.m\.|p\.m\.)?', 'standard'),
        (r'(\d{1,2})\s+(\d{2})\s*(am|pm|a\.m\.|p\.m\.)', 'spaced'),  # 12h spaced
        (r'at\s+(\d{1,2})\s+(\d{2})\s*(am|pm|a\.m\.|p\.m\.)', 'at_spaced'),
        (r'(\d{1,2})\s+(\d{2})(?!\s*(am|pm|a\.m\.|p\.m\.))', 'spaced_24h'),  # 24h spaced (no AM/PM)
        (r'(\d{1,2})\.(\d{2})\s*(am|pm|a\.m\.|p\.m\.)?', 'dot'),
        (r'at\s+(\d{1,2})\.(\d{2})\s*(am|pm|a\.m\.|p\.m\.)?', 'at_dot'),
        # 12-hour format patterns
        (r'(\d{1,2})\s*(am|pm|a\.m\.|p\.m\.)', 'simple'),
        (r'at\s+(\d{1,2}):(\d{2})\s*(am|pm|a\.m\.|p\.m\.)?', 'at_standard'),
        (r'at\s+(\d{1,2})\s*(am|pm|a\.m\.|p\.m\.)', 'at_simple'),
        # Relative time patterns
        (r'in\s+(\d+)\s+(minute|minutes|min|mins)', 'relative_minutes'),
        (r'in\s+(\d+)\s+(hour|hours|hr|hrs)', 'relative_hours'),
        (r'in\s+(\d+)\s+and\s+a\s+half\s+(hour|hours)', 'relative_half_hour'),
    ]
    
    # Named time references (for elderly users)
    NAMED_TIMES = {
        # Morning times
        'morning': '08:00',
        'early morning': '06:00',
        'breakfast': '08:00',
        'breakfast time': '08:00',
        'sunrise': '06:30',
        # Noon times
        'noon': '12:00',
        'midday': '12:00',
        'lunch': '12:30',
        'lunch time': '12:30',
        'afternoon': '15:00',
        'late afternoon': '16:00',
        # Evening times
        'evening': '18:00',
        'dinner': '19:00',
        'dinner time': '19:00',
        'supper': '19:00',
        'supper time': '19:00',
        'late evening': '20:00',
        # Night times
        'night': '21:00',
        'bedtime': '22:00',
        'sleep time': '22:00',
        'midnight': '00:00',
        'late night': '23:00',
        # Additional elderly-friendly times
        'medicine time': '08:00',
        'tea time': '16:00',
        'cocktail hour': '17:00',
    }
    
    # Date patterns
    DATE_PATTERNS = [
        (r'today', 'today'),
        (r'tomorrow', 'tomorrow'),
        (r'day after tomorrow', 'day_after_tomorrow'),
        (r'next\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)', 'next_weekday'),
        (r'on\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)', 'on_weekday'),
        (r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})', 'date_format'),
        (r'(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2})', 'month_day'),
    ]
    
    # Task extraction patterns (what to remind about)
    TASK_PATTERNS = [
        r'to\s+(.+?)(?:\s+at|\s+on|\s+in|\s+for|$)',
        r'about\s+(.+?)(?:\s+at|\s+on|\s+in|\s+for|$)',
        r'for\s+(.+?)(?:\s+at|\s+on|\s+in|$)',
        r'that\s+(.+?)(?:\s+at|\s+on|\s+in|$)',
    ]
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def is_reminder_request(self, text: str) -> bool:
        """Check if the text is a reminder/alarm request"""
        text_lower = text.lower()
        return any(re.search(pattern, text_lower) for pattern in self.REMINDER_PATTERNS)
    
    def extract_time(self, text: str) -> Optional[str]:
        """Extract time from text and convert to HH:MM format"""
        text_lower = text.lower()
        
        # Check named times first
        for name, time_str in self.NAMED_TIMES.items():
            if name in text_lower:
                return time_str
        
        # Check time patterns
        for pattern, pattern_type in self.TIME_PATTERNS:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                if pattern_type in ['military', 'military_simple']:
                    # Handle "19 hundred hours" -> 19:00
                    hour = int(match.group(1))
                    minute = 0  # Hundred hours always means :00
                    # Validate 24-hour format
                    if 0 <= hour <= 23:
                        return f"{hour:02d}:00"
                    else:
                        logging.warning(f"Invalid military hour: {hour}")
                        continue
                elif pattern_type == 'hours_format':
                    # Handle "19 hours" -> 19:00
                    hour = int(match.group(1))
                    minute = 0
                    if 0 <= hour <= 23:
                        return f"{hour:02d}:00"
                    else:
                        logging.warning(f"Invalid hour: {hour}")
                        continue
                elif pattern_type in ['standard', 'at_standard']:
                    hour = int(match.group(1))
                    minute = int(match.group(2))
                    period = match.group(3).lower() if len(match.groups()) > 2 and match.group(3) else None
                    # Check if it's 24-hour format (no AM/PM and hour > 12)
                    if not period and hour > 12 and hour <= 23:
                        return f"{hour:02d}:{minute:02d}"
                    return self._format_24h_time(hour, minute, period)
                elif pattern_type in ['dot', 'at_dot']:
                    hour = int(match.group(1))
                    minute = int(match.group(2))
                    period = match.group(3).lower() if len(match.groups()) > 2 and match.group(3) else None
                    # Check if it's 24-hour format
                    if not period and hour > 12 and hour <= 23:
                        return f"{hour:02d}:{minute:02d}"
                    return self._format_24h_time(hour, minute, period)
                elif pattern_type == 'spaced_24h':
                    # Handle "19 30" -> 19:30 (24-hour format)
                    hour = int(match.group(1))
                    minute = int(match.group(2))
                    # Check if it's 24-hour format
                    if 0 <= hour <= 23 and 0 <= minute <= 59:
                        return f"{hour:02d}:{minute:02d}"
                    else:
                        logging.warning(f"Invalid 24h time: {hour}:{minute}")
                        continue
                elif pattern_type in ['spaced', 'at_spaced']:
                    hour = int(match.group(1))
                    minute = int(match.group(2))
                    period = match.group(3).lower() if len(match.groups()) > 2 and match.group(3) else None
                    # Check if it's 24-hour format
                    if not period and hour > 12 and hour <= 23:
                        return f"{hour:02d}:{minute:02d}"
                    return self._format_24h_time(hour, minute, period)
                elif pattern_type in ['simple', 'at_simple']:
                    hour = int(match.group(1))
                    minute = 0  # Default to 0 minutes
                    period = match.group(2).lower() if len(match.groups()) > 1 and match.group(2) else None
                    # Check if it's 24-hour format
                    if not period and hour > 12 and hour <= 23:
                        return f"{hour:02d}:00"
                    return self._format_24h_time(hour, minute, period)
        
        return None
    
    def _format_24h_time(self, hour: int, minute: int, period: Optional[str] = None) -> str:
        """Convert 12-hour time to 24-hour format"""
        if period:
            if 'pm' in period and hour < 12:
                hour += 12
            elif 'am' in period and hour == 12:
                hour = 0
        return f"{hour:02d}:{minute:02d}"
    
    def extract_task(self, text: str) -> str:
        """Extract task/description from reminder text"""
        text_lower = text.lower()
        
        # First check for alarm/reminder/wake-up keywords with following message
        if re.search(r'\balarm\b', text, re.IGNORECASE):
            # Look for message after "alarm" keyword
            alarm_match = re.search(r'alarm\s+(.+?)(?:\s+at|\s+for|\s+in|$)', text, re.IGNORECASE)
            if alarm_match:
                task = alarm_match.group(1).strip()
                # If task is just a time, use default
                if re.match(r'^\d{1,2}[:\s]\d{2}\s*(am|pm|a\.m\.|p\.m\.)?$', task, re.IGNORECASE) or \
                   re.match(r'^\d{1,2}\s*(am|pm|a\.m\.|p\.m\.)?$', task, re.IGNORECASE) or \
                   re.match(r'^\d{1,2}\s+hundred', task, re.IGNORECASE):
                    return "Alarm"
                return task if task else "Alarm"
        elif re.search(r'\breminder\b', text, re.IGNORECASE):
            # Look for message after "reminder" keyword  
            reminder_match = re.search(r'reminder\s+(.+?)(?:\s+at|\s+for|\s+in|$)', text, re.IGNORECASE)
            if reminder_match:
                task = reminder_match.group(1).strip()
                # If task is just a time, use default
                if re.match(r'^\d{1,2}[:\s]\d{2}\s*(am|pm|a\.m\.|p\.m\.)?$', task, re.IGNORECASE) or \
                   re.match(r'^\d{1,2}\s*(am|pm|a\.m\.|p\.m\.)?$', task, re.IGNORECASE) or \
                   re.match(r'^\d{1,2}\s+hundred', task, re.IGNORECASE):
                    return "Reminder"
                return task if task else "Reminder"
        elif re.search(r'\bwake\s+me\s+up\b', text, re.IGNORECASE):
            return "Wake up"
        elif re.search(r'\bcall\b', text, re.IGNORECASE):
            return "Call"
        
        # Handle "set alarm for [time]" pattern
        set_alarm_match = re.search(r'set\s+alarm\s+(?:for|at)\s+(.+)', text, re.IGNORECASE)
        if set_alarm_match:
            remaining = set_alarm_match.group(1).strip()
            # If remaining is just a time, use default
            if re.match(r'^\d{1,2}[:\s]\d{2}\s*(am|pm|a\.m\.|p\.m\.)?$', remaining, re.IGNORECASE) or \
               re.match(r'^\d{1,2}\s*(am|pm|a\.m\.|p\.m\.)?$', remaining, re.IGNORECASE) or \
               re.match(r'^\d{1,2}\s+hundred', remaining, re.IGNORECASE) or \
               remaining in ['morning', 'evening', 'night', 'bedtime', 'dinner time', 'lunch time']:
                return "Alarm"
            return remaining
        
        # Handle "set reminder for [time]" pattern
        set_reminder_match = re.search(r'set\s+reminder\s+(?:for|at)\s+(.+)', text, re.IGNORECASE)
        if set_reminder_match:
            remaining = set_reminder_match.group(1).strip()
            # If remaining is just a time, use default
            if re.match(r'^\d{1,2}[:\s]\d{2}\s*(am|pm|a\.m\.|p\.m\.)?$', remaining, re.IGNORECASE) or \
               re.match(r'^\d{1,2}\s*(am|pm|a\.m\.|p\.m\.)?$', remaining, re.IGNORECASE) or \
               re.match(r'^\d{1,2}\s+hundred', remaining, re.IGNORECASE) or \
               remaining in ['morning', 'evening', 'night', 'bedtime', 'dinner time', 'lunch time']:
                return "Reminder"
            return remaining
        
        # Then try specific patterns for detailed tasks
        for pattern in self.TASK_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                task = match.group(1).strip()
                # Make sure extracted task is not just a time
                if not re.match(r'^\d{1,2}[:\s]\d{2}\s*(am|pm|a\.m\.|p\.m\.)?$', task, re.IGNORECASE) and \
                   not re.match(r'^\d{1,2}\s*(am|pm|a\.m\.|p\.m\.)?$', task, re.IGNORECASE) and \
                   not re.match(r'^\d{1,2}\s+hundred', task, re.IGNORECASE):
                    return task
        
        return "Reminder"  # Default task if none found


def process_reminder_request(text: str) -> Optional[ReminderResponse]:
    """
    Process a natural language reminder request.
    
    Args:
        text: User's input text (e.g., "remind me to take medicine at 8pm")
        
    Returns:
        Optional[ReminderResponse]: Response tuple if it's a reminder request, None otherwise
    """
    try:
        parser = ReminderParser()
        manager = ReminderManager()
        
        # Check if this is a reminder request
        if not parser.is_reminder_request(text):
            return None
            
        # Extract time and task from the request
        time_str = parser.extract_time(text)
        task = parser.extract_task(text)
        
        # Enhanced validation for elderly users
        if not time_str:
            # Try to guess time from context for elderly users
            text_lower = text.lower()
            if 'medicine' in text_lower or 'pill' in text_lower:
                time_str = '08:00'  # Default medicine time
                logging.info(f"Guessed medicine time: {time_str}")
            elif 'wake' in text_lower or 'morning' in text_lower:
                time_str = '07:00'  # Default wake time
                logging.info(f"Guessed wake time: {time_str}")
            else:
                return ReminderResponse(
                    "I didn't understand the time. Please say it like '8 AM', '19 hundred hours', or 'dinner time'.",
                    "❌ Could not understand time. Try: '8 AM', '19:00', '7 PM', or 'dinner time'"
                )
        
        if not task or task.strip() == '':
            return ReminderResponse(
                "What should I remind you about?",
                "❌ Please tell me what to remind you about"
            )
            
        # Validate the extracted time format
        try:
            time_obj = datetime.strptime(time_str, "%H:%M")
            if not (0 <= time_obj.hour <= 23 and 0 <= time_obj.minute <= 59):
                raise ValueError("Invalid time range")
        except ValueError:
            return ReminderResponse(
                f"The time '{time_str}' doesn't look right. Please try again.",
                f"❌ Invalid time format: {time_str}"
            )
            
        # Add the reminder (default to daily repeat)
        success = manager.add_reminder(
            task=task,
            time_str=time_str,
            repeat_daily=True,
            ring_enabled=True
        )
        
        if success:
            # Generate natural response based on task type and time
            time_display = time_str
            try:
                # Convert to 12-hour format for elderly users
                time_obj = datetime.strptime(time_str, "%H:%M")
                if time_obj.hour == 0:
                    time_display = "12 AM"
                elif time_obj.hour < 12:
                    time_display = f"{time_obj.hour} AM"
                elif time_obj.hour == 12:
                    time_display = "12 PM"
                else:
                    time_display = f"{time_obj.hour - 12} PM"
                
                if time_obj.minute > 0:
                    time_display = f"{time_obj.hour:02d}:{time_obj.minute:02d}"
            except:
                pass  # Keep original format if conversion fails
            
            # Generate friendly response
            if task.lower() in ['alarm', 'reminder']:
                response = f"I'll set an alarm for {time_display}"
                display_text = f"✅ Alarm set for {time_display}"
            elif task.lower() == 'wake up':
                response = f"I'll wake you up at {time_display}"
                display_text = f"✅ Wake-up alarm set for {time_display}"
            elif 'medicine' in task.lower():
                response = f"I'll remind you to take your medicine at {time_display}"
                display_text = f"✅ Medicine reminder set for {time_display}"
            else:
                response = f"I'll remind you to {task} at {time_display}"
                display_text = f"✅ Reminder set: {task} at {time_display}"
            
            logging.info(f"✅ Successfully set reminder: {task} at {time_str}")
            return ReminderResponse(
                spoken_text=response,
                display_text=display_text,
                reminder_data={"task": task, "time": time_str, "display_time": time_display}
            )
        else:
            return ReminderResponse(
                "I couldn't set that reminder. Please try again.",
                "❌ Failed to set reminder - please try again"
            )
            
    except Exception as e:
        logging.error(f"Error processing reminder request: {e}")
        return ReminderResponse(
            "I had trouble setting that reminder. Please try again.",
            f"❌ Error: {str(e)}"
        )


# =============================================================================
# Reminder Manager Module
# =============================================================================

class ReminderManager:
    """Manages reminders in the database"""
    
    def __init__(self, db_path: str = None):
        self.db_path = str(db_path) if db_path else str(DB_PATH)
        self.parser = ReminderParser()
    
    def add_reminder(self, task: str, time_str: str, repeat_daily: bool = True, ring_enabled: bool = True, custom_ringtone: str = None) -> bool:
        """Add a new reminder to the database"""
        conn = None
        try:
            # Validate time format
            try:
                time_obj = datetime.strptime(time_str, "%H:%M")
            except ValueError:
                logging.error(f"Invalid time format: {time_str}. Expected HH:MM (24-hour)")
                return False
            
            # Create timestamp for the reminder
            now = datetime.now()
            timestamp = now.replace(
                hour=time_obj.hour,
                minute=time_obj.minute,
                second=0,
                microsecond=0
            ).isoformat()
            
            conn = sqlite3.connect(self.db_path, timeout=20)
            cursor = conn.cursor()
            
            # Create table if it doesn't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task TEXT NOT NULL,
                    time TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    repeat_daily BOOLEAN DEFAULT 1,
                    ring_enabled BOOLEAN DEFAULT 1,
                    is_active BOOLEAN DEFAULT 1,
                    last_run TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    custom_ringtone TEXT
                )
            ''')
            
            cursor.execute('''
                INSERT INTO reminders (task, time, timestamp, repeat_daily, ring_enabled, custom_ringtone)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (task, time_str, timestamp, repeat_daily, ring_enabled, custom_ringtone))
            
            conn.commit()
            logging.info(f"✅ Added reminder: {time_str} - {task} (Daily: {repeat_daily}, Ring: {ring_enabled}, Custom: {custom_ringtone})")
            return True
            
        except Exception as e:
            logging.error(f"❌ Error adding reminder: {str(e)}")
            return False
        finally:
            if conn:
                conn.close()
    
    def fetch_reminders(self) -> List[Dict]:
        """Fetch all active reminders from the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM reminders 
                WHERE is_active = 1
                ORDER BY time
            ''')
            
            return [dict(row) for row in cursor.fetchall()]
            
        except Exception as e:
            logging.error(f"❌ Error fetching reminders: {str(e)}")
            return []
        finally:
            if 'conn' in locals():
                conn.close()
    
    def update_reminder_last_run(self, reminder_id: int) -> bool:
        """Update the last_run timestamp after reminder is triggered"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE reminders 
                SET last_run = ?
                WHERE id = ?
            ''', (datetime.now().isoformat(), reminder_id))
            
            conn.commit()
            return True
            
        except Exception as e:
            logging.error(f"❌ Error updating reminder last_run: {str(e)}")
            return False
        finally:
            if 'conn' in locals():
                conn.close()
    
    def delete_reminder(self, reminder_id: int) -> bool:
        """Soft delete a reminder by setting is_active to False"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE reminders 
                SET is_active = 0
                WHERE id = ?
            ''', (reminder_id,))
            
            conn.commit()
            return True
            
        except Exception as e:
            logging.error(f"❌ Error deleting reminder: {str(e)}")
            return False
        finally:
            if 'conn' in locals():
                conn.close()
    
    def get_reminder_by_id(self, reminder_id: int) -> Optional[Dict]:
        """Get a specific reminder by ID"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM reminders 
                WHERE id = ? AND is_active = 1
            ''', (reminder_id,))
            
            row = cursor.fetchone()
            return dict(row) if row else None
            
        except Exception as e:
            logging.error(f"❌ Error getting reminder: {str(e)}")
            return None
        finally:
            if 'conn' in locals():
                conn.close()
