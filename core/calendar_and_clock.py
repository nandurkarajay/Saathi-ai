"""
Calendar and Clock module for Sathi AI assistant.
Provides elderly-friendly time, date, and calendar information through voice interaction.
Focuses on clear, simple responses suitable for elderly users.
"""

import datetime
import calendar
import re
from typing import Tuple, Optional
import logging

# Configure logging
logging.basicConfig(
    filename='data/calendar_clock.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Intent patterns for time/date queries - comprehensive patterns for elderly users
TIME_PATTERNS = [
    r"what(?:'s| is) the time",
    r"tell me the time",
    r"current time",
    r"time now",
    r"what time (is it|do we have)",
    r"(?:can you )?tell me what time it is",
    r"do you know the time",
    r"check the time",
]

DATE_PATTERNS = [
    r"what(?:'s| is) (?:the )?date(?:.*?today)?",
    r"today's date",
    r"what (?:is the )?date",
    r"tell me (?:the |today's )?date",
    r"(?:can you )?tell me (?:the )?date",
    r"what (?:is the )?date (?:today|now)",
    r"what day of the month is it",
    r"which date is (?:it|today)",
    r"(?:what|which) date (?:do we have|is it)",
    r"date please",
    r"give me the date",
    r"today's date",
    r"(?:what|which) date",
    r"date",
]

DAY_PATTERNS = [
    r"what day is (?:it|today)",
    r"which day is (?:it|today)",
    r"tell me the day",
    r"(?:can you )?tell me what day it is",
    r"what day of the week is it",
    r"is it (monday|tuesday|wednesday|thursday|friday|saturday|sunday)",
]

CALENDAR_PATTERNS = [
    r"(?:read|tell) me this month's calendar",
    r"how many days (?:are )?(?:in|this) (?:this )?month",
    r"tell me about this month",
    r"what month is it",
    r"give me (?:the )?month(?:'s)? details",
    r"tell me about (?:the )?current month",
    r"how long is this month",
]

def detect_time_intent(text: str) -> bool:
    """Check if input contains a time-related query."""
    return any(re.search(pattern, text.lower()) for pattern in TIME_PATTERNS)

def detect_date_intent(text: str) -> bool:
    """Check if input contains a date-related query."""
    return any(re.search(pattern, text.lower()) for pattern in DATE_PATTERNS)

def detect_day_intent(text: str) -> bool:
    """Check if input contains a day-of-week query."""
    return any(re.search(pattern, text.lower()) for pattern in DAY_PATTERNS)

def detect_calendar_intent(text: str) -> bool:
    """Check if input contains a calendar-related query."""
    return any(re.search(pattern, text.lower()) for pattern in CALENDAR_PATTERNS)

def get_current_time() -> Tuple[str, str]:
    """
    Get current time in both spoken and display formats.
    Returns: (spoken_response, display_text)
    """
    try:
        now = datetime.datetime.now()
        
        # Windows-compatible way to get hour and minute without leading zeros
        hour = now.hour % 12
        if hour == 0:
            hour = 12
        minute = now.minute
        meridian = "pm" if now.hour >= 12 else "am"
        
        # More natural minute expressions
        if minute == 0:
            minute_str = "o'clock"
        elif minute < 10:
            minute_str = f"oh {minute}"
        else:
            minute_str = str(minute)
        
        spoken = f"It's {hour} {minute_str} {meridian}"
        display = f"🕐 {now.strftime('%I:%M %p')}"
        logging.info(f"Time request - Responded with: {spoken}")
        return spoken, display
        
    except Exception as e:
        logging.error(f"Error getting current time: {str(e)}")
        return ("I'm having trouble reading the time right now.", 
                "⚠️ Error reading time")

def get_ordinal_suffix(day: int) -> str:
    """Helper function to get the ordinal suffix for a day number."""
    if 10 <= day % 100 <= 20:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')
    return f"{day}{suffix}"

def get_current_date() -> Tuple[str, str]:
    """
    Get current date in both spoken and display formats.
    Returns: (spoken_response, display_text)
    """
    try:
        now = datetime.datetime.now()
        
        # Get date components safely
        try:
            weekday = now.strftime('%A')
            month = now.strftime('%B')
        except Exception as e:
            logging.error(f"Error formatting date components: {str(e)}")
            # Fallback to basic names
            weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            months = ['January', 'February', 'March', 'April', 'May', 'June', 
                     'July', 'August', 'September', 'October', 'November', 'December']
            weekday = weekdays[now.weekday()]
            month = months[now.month - 1]
        
        day = now.day
        year = now.year
        
        # Get day with ordinal suffix
        day_str = get_ordinal_suffix(day)
        
        # Construct elderly-friendly responses with clear pauses
        spoken = f"Today is {weekday}, {month} {day_str}, {year}"
        display = f"📅 {weekday}, {month} {day}, {year}"
        
        logging.info(f"Successfully generated date response: {spoken}")
        return spoken, display
        
    except Exception as e:
        error_msg = f"Error getting current date: {str(e)}"
        logging.error(error_msg)
        try:
            # Extremely basic fallback
            now = datetime.datetime.now()
            basic_response = f"Today is {now.month}/{now.day}/{now.year}"
            return (basic_response, f"📅 {basic_response}")
        except:
            return ("I'm having trouble reading today's date. Please try asking me again in a moment.",
                    "⚠️ Error reading date")

def get_current_day() -> Tuple[str, str]:
    """
    Get current day of week in both spoken and display formats.
    Returns: (spoken_response, display_text)
    """
    now = datetime.datetime.now()
    day_name = now.strftime('%A')
    spoken = f"Today is {day_name}"
    display = f"📅 {day_name}"
    logging.info(f"Day request - Responded with: {spoken}")
    return spoken, display

def get_month_calendar() -> Tuple[str, str]:
    """
    Get current month's calendar information in both spoken and display formats.
    Returns: (spoken_response, display_text)
    """
    now = datetime.datetime.now()
    month_name = now.strftime("%B")
    num_days = calendar.monthrange(now.year, now.month)[1]
    start_day = calendar.day_name[calendar.monthrange(now.year, now.month)[0]]
    
    spoken = (f"We are in the month of {month_name}. "
             f"This month has {num_days} days in total. "
             f"The first day of {month_name} was a {start_day}. "
             f"Today is day number {now.day} of the month.")
    
    display = (f"📅 {month_name} {now.year}\n"
              f"• Days in month: {num_days}\n"
              f"• Started on: {start_day}\n"
              f"• Current day: {now.day} of {num_days}")
    
    logging.info(f"Calendar request - Responded with summary for {month_name}")
    return spoken, display

def process_time_query(text: str) -> Optional[Tuple[str, str]]:
    """
    Process a time/date related query and return appropriate response.
    Returns: (spoken_response, display_text) or None if not a time query
    Handles errors gracefully with elderly-friendly error messages.
    """
    try:
        if not text:
            logging.warning("Empty query received")
            return ("I didn't quite catch that. Could you please repeat your question?",
                    "⚠️ Could not understand the query")

        text = text.lower().strip()
        logging.info(f"Processing query: {text}")
        
        # First try exact pattern matching
        try:
            if detect_date_intent(text):  # Check date first since it's more specific
                logging.info("Date intent detected")
                return get_current_date()
            elif detect_time_intent(text):
                logging.info("Time intent detected")
                return get_current_time()
            elif detect_day_intent(text):
                logging.info("Day intent detected")
                return get_current_day()
            elif detect_calendar_intent(text):
                logging.info("Calendar intent detected")
                return get_month_calendar()
            
            # If no exact match, try partial matching for common words
            if any(word in text for word in ['date', 'today', 'day', 'month']):
                logging.info("Partial date match detected")
                return get_current_date()
            elif any(word in text for word in ['time', 'clock', 'hour']):
                logging.info("Partial time match detected")
                return get_current_time()
                
        except Exception as e:
            logging.error(f"Error in intent processing: {str(e)}")
            return ("I'm having trouble getting that information right now. Please try asking in a simpler way.",
                    "⚠️ Error processing query")
        
        return None
        
    except Exception as e:
        logging.error(f"Unexpected error in process_time_query: {str(e)}")
        return ("I apologize, but I'm having difficulty understanding. Could you please repeat that?",
                "⚠️ System error")