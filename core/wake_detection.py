"""
Wake Detection Module
Combines wake word detection, audio processing, and time/date functionality
for the Sathi AI assistant.
"""

# Standard library imports
import sys
import re
import logging
import datetime
import calendar
from pathlib import Path
from typing import Tuple, Optional, Union, List

# Third-party imports
import numpy as np

# Add project root to path for local imports
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Local imports
from core.voice_input import transcribe_audio
from core.utils import is_wake_word

# Configure logging
logging.basicConfig(
    filename='data/wake_detection.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# =============================================================================
# Audio Wake Detection
# =============================================================================

def calculate_audio_energy(audio_data: np.ndarray) -> float:
    """Calculate the energy/volume of audio signal."""
    return np.sqrt(np.mean(audio_data**2))

def detect_speech_pattern(audio_path: str, min_energy_threshold: float = 500) -> bool:
    """
    Detect if audio contains speech-like patterns.
    
    Args:
        audio_path: Path to the audio file
        min_energy_threshold: Minimum energy threshold for speech detection
        
    Returns:
        bool: True if speech is detected, False otherwise
    """
    try:
        sample_rate, audio_data = wavfile.read(audio_path)
        
        # Convert to mono if stereo
        if len(audio_data.shape) > 1:
            audio_data = audio_data.mean(axis=1)
        
        # Calculate energy
        energy = calculate_audio_energy(audio_data)
        
        # Check if energy is above threshold (indicates speech)
        if energy < min_energy_threshold:
            return False
        
        # Split audio into frames and check for speech-like patterns
        frame_length = int(0.03 * sample_rate)  # 30ms frames
        num_frames = len(audio_data) // frame_length
        
        speech_frames = 0
        for i in range(num_frames):
            frame = audio_data[i * frame_length:(i + 1) * frame_length]
            frame_energy = calculate_audio_energy(frame)
            
            if frame_energy > min_energy_threshold * 0.5:
                speech_frames += 1
        
        # If more than 20% of frames have speech-like energy, consider it speech
        speech_ratio = speech_frames / num_frames if num_frames > 0 else 0
        return speech_ratio > 0.2
        
    except Exception as e:
        logging.error(f"Error in speech pattern detection: {e}")
        return False

def simple_wake_word_check(audio_path: str) -> bool:
    """
    Simple heuristic-based wake word detection.
    Checks if audio has the right duration and energy pattern for "hey sathi".
    
    Args:
        audio_path: Path to the audio file
        
    Returns:
        bool: True if the audio matches the wake word pattern
    """
    try:
        sample_rate, audio_data = wavfile.read(audio_path)
        
        # Convert to mono
        if len(audio_data.shape) > 1:
            audio_data = audio_data.mean(axis=1)
        
        # "Hey Sathi" is typically 0.8-1.5 seconds
        duration = len(audio_data) / sample_rate
        
        if duration < 0.5 or duration > 3.0:
            return False
        
        # Check for two-word pattern (two energy peaks)
        frame_length = int(0.1 * sample_rate)  # 100ms frames
        num_frames = len(audio_data) // frame_length
        
        energies = []
        for i in range(num_frames):
            frame = audio_data[i * frame_length:(i + 1) * frame_length]
            energies.append(calculate_audio_energy(frame))
        
        if len(energies) < 2:
            return False
        
        # Look for two peaks (two words)
        energies = np.array(energies)
        mean_energy = np.mean(energies)
        peaks = energies > (mean_energy * 1.2)
        
        # Count number of peak regions
        peak_regions = 0
        in_peak = False
        for peak in peaks:
            if peak and not in_peak:
                peak_regions += 1
                in_peak = True
            elif not peak:
                in_peak = False
        
        # "Hey Sathi" should have 1-3 peak regions
        return 1 <= peak_regions <= 3
        
    except Exception as e:
        logging.error(f"Error in simple wake word check: {e}")
        return False

def audio_based_wake_detection(audio_path: str) -> float:
    """
    Main function for audio-based wake word detection.
    
    Args:
        audio_path: Path to the audio file
        
    Returns:
        float: Confidence score between 0.0 and 1.0
    """
    # Check if speech is present
    has_speech = detect_speech_pattern(audio_path)
    if not has_speech:
        return 0.0
    
    # Check if pattern matches "hey sathi"
    matches_pattern = simple_wake_word_check(audio_path)
    
    if matches_pattern:
        return 0.7  # Return moderate confidence
    elif has_speech:
        return 0.3  # Has speech but doesn't match pattern
    else:
        return 0.0

# =============================================================================
# Hybrid Wake Detection
# =============================================================================

def hybrid_wake_word_detection(audio_path: str, verbose: bool = True) -> Tuple[bool, float, str]:
    """
    Hybrid wake word detection using multiple methods.
    
    Args:
        audio_path: Path to the audio file
        verbose: Whether to print debug information
        
    Returns:
        tuple: (detected: bool, confidence: float, method: str)
    """
    # Method 1: Try Whisper transcription with wake word prompt
    if verbose:
        print("\n🔍 Method 1: Whisper Transcription...")
    
    transcription = transcribe_audio(audio_path, is_wake_word=True)
    
    text_score = 0.0
    audio_score = 0.0
    
    if transcription and transcription.lower() != "(speaking in foreign language)":
        # Valid transcription received
        text_score = is_wake_word(transcription)
        
        if text_score >= 0.65:
            if verbose:
                print(f"✅ Whisper detected wake word! Score: {text_score:.2f}")
            return True, text_score, "whisper"
        elif verbose:
            print(f"⚠️ Whisper transcribed but low score: {text_score:.2f}")
    else:
        if verbose:
            print("⚠️ Whisper failed or detected foreign language")
    
    # Method 2: Audio pattern matching (fallback)
    if verbose:
        print("\n🔍 Method 2: Audio Pattern Matching...")
    
    try:
        audio_score = audio_based_wake_detection(audio_path)
        
        if audio_score >= 0.6:
            if verbose:
                print(f"✅ Audio pattern matched! Score: {audio_score:.2f}")
            return True, audio_score, "audio_pattern"
        elif verbose:
            print(f"⚠️ Audio pattern score too low: {audio_score:.2f}")
    except Exception as e:
        if verbose:
            print(f"⚠️ Audio pattern matching failed: {e}")
    
    # Method 3: Combined heuristic
    # If Whisper gave us something and audio pattern shows speech
    if 'transcription' in locals() and transcription and audio_score > 0.3:
        combined_score = (text_score * 0.6 + audio_score * 0.4)
        if combined_score >= 0.5:
            if verbose:
                print(f"✅ Combined heuristic matched! Score: {combined_score:.2f}")
            return True, combined_score, "combined"
    
    # No detection
    if verbose:
        print("❌ No wake word detected by any method")
    return False, 0.0, "none"

# =============================================================================
# Time and Date Functionality
# =============================================================================

# Intent patterns for time/date queries
DATETIME_PATTERNS = [
    r"(?:what|tell me|give me)(?:'s| is)?(?: the)? (?:current )?(?:time and date|date and time)",
    r"what(?:'s| is) today's date and time",
    r"tell me (?:the |today's )?(?:time and date|date and time)",
    r"current time and date",
    r"what time and date is it",
]

DATETIME_DAY_PATTERNS = [
    r"(?:what|tell me|give me)(?:'s| is)?(?: the)? (?:current )?(?:time,? date,? and day|date,? time,? and day)",
    r"tell me (?:the )?(?:time,? date,? and day|date,? time,? and day) (?:today|now)",
    r"what(?:'s| is) today's date,? time,? and day",
    r"tell me everything about (?:today|now|the current time)",
    r"what day,? date,? and time is it",
]

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

def detect_datetime_intent(text: str) -> bool:
    """Check if input contains a combined date and time query."""
    return any(re.search(pattern, text.lower()) for pattern in DATETIME_PATTERNS)

def detect_datetime_day_intent(text: str) -> bool:
    """Check if input contains a combined date, time and day query."""
    return any(re.search(pattern, text.lower()) for pattern in DATETIME_DAY_PATTERNS)

def get_current_time() -> Tuple[str, str]:
    """
    Get current time in both spoken and display formats.
    
    Returns:
        tuple: (spoken_response, display_text)
    """
    try:
        now = datetime.datetime.now()
        
        # 12-hour format with AM/PM
        time_12hr = now.strftime("%I:%M %p")
        # Remove leading zero if present
        if time_12hr[0] == '0':
            time_12hr = time_12hr[1:]
            
        # 24-hour format
        time_24hr = now.strftime("%H:%M")
        
        # Create spoken response
        hour = now.hour
        minute = now.minute
        
        # Convert to 12-hour format for speaking
        period = "AM" if hour < 12 else "PM"
        hour_12 = hour % 12
        if hour_12 == 0:
            hour_12 = 12
            
        if minute == 0:
            spoken_time = f"{hour_12} {period}"
        elif minute < 10:
            spoken_time = f"{hour_12} oh {minute} {period}"
        else:
            spoken_time = f"{hour_12} {minute} {period}"
            
        display_text = f"The current time is {time_12hr} ({time_24hr})"
        return spoken_time, display_text
        
    except Exception as e:
        logging.error(f"Error getting current time: {e}")
        return "I'm sorry, I couldn't get the current time.", "Error getting time"

def get_ordinal_suffix(day: int) -> str:
    """Helper function to get the ordinal suffix for a day number."""
    if 11 <= (day % 100) <= 13:
        return 'th'
    else:
        return {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')

def get_current_date() -> Tuple[str, str]:
    """
    Get current date in both spoken and display formats.
    
    Returns:
        tuple: (spoken_response, display_text)
    """
    try:
        now = datetime.datetime.now()
        
        # Get day with ordinal suffix
        day = now.day
        suffix = get_ordinal_suffix(day)
        
        # Format date in different ways
        month_name = now.strftime("%B")
        year = now.year
        
        # US format: Month Day, Year
        us_format = f"{month_name} {day}{suffix}, {year}"
        
        # International format: Day Month Year
        intl_format = f"{day}{suffix} {month_name} {year}"
        
        # Spoken response
        spoken_date = f"{month_name} {day}{suffix}, {year}"
        
        # Display text
        display_text = f"Today is {us_format} (or {intl_format} in international format)"
        
        return spoken_date, display_text
        
    except Exception as e:
        logging.error(f"Error getting current date: {e}")
        return "I'm sorry, I couldn't get today's date.", "Error getting date"

def get_current_day() -> Tuple[str, str]:
    """
    Get current day of week in both spoken and display formats.
    
    Returns:
        tuple: (spoken_response, display_text)
    """
    try:
        now = datetime.datetime.now()
        day_name = now.strftime("%A")
        
        spoken_day = f"It's {day_name}"
        display_text = f"Today is {day_name}"
        
        return spoken_day, display_text
        
    except Exception as e:
        logging.error(f"Error getting current day: {e}")
        return "I'm sorry, I couldn't get the current day.", "Error getting day"

def get_month_calendar() -> Tuple[str, str]:
    """
    Get current month's calendar information in both spoken and display formats.
    
    Returns:
        tuple: (spoken_response, display_text)
    """
    try:
        now = datetime.datetime.now()
        year = now.year
        month = now.month
        
        # Get calendar for the current month
        cal = calendar.monthcalendar(year, month)
        month_name = now.strftime("%B")
        
        # Count number of days in the month
        _, num_days = calendar.monthrange(year, month)
        
        # Get the day of week for the first day of the month (0=Monday, 6=Sunday)
        first_day = calendar.monthrange(year, month)[0]
        
        # Create a simple calendar display
        cal_text = calendar.month_name[month] + " " + str(year) + "\n"
        cal_text += "Mo Tu We Th Fr Sa Su\n"
        
        # Add leading spaces for the first week
        cal_text += "   " * first_day
        
        # Add the days
        day = 1
        for i in range(first_day, 7):
            cal_text += f"{day:2d} "
            day += 1
        cal_text += "\n"
        
        # Add the remaining weeks
        while day <= num_days:
            for i in range(7):
                if day > num_days:
                    break
                cal_text += f"{day:2d} "
                day += 1
            cal_text += "\n"
        
        # Create spoken response
        spoken = f"The current month is {month_name} {year}. "
        spoken += f"It has {num_days} days. "
        
        # Add information about current day
        today = now.day
        spoken += f"Today is {month_name} {today}{get_ordinal_suffix(today)}."
        
        return spoken, cal_text
        
    except Exception as e:
        logging.error(f"Error getting month calendar: {e}")
        return "I'm sorry, I couldn't get the calendar information.", "Error getting calendar"

def process_time_query(text: str) -> Optional[Tuple[str, str]]:
    """
    Process a time/date related query and return appropriate response.
    
    Args:
        text: The user's query text
        
    Returns:
        tuple: (spoken_response, display_text) or None if not a time query
    """
    try:
        text = text.lower().strip()
        
        # Check for combined date, time, and day query first (most specific)
        if detect_datetime_day_intent(text):
            time_spoken, time_display = get_current_time()
            date_spoken, date_display = get_current_date()
            day_spoken, day_display = get_current_day()
            
            spoken = f"{time_spoken}. {date_spoken}. {day_spoken}."
            display = f"{time_display}\n{date_display}\n{day_display}"
            return spoken, display
            
        # Check for date and time query
        elif detect_datetime_intent(text):
            time_spoken, time_display = get_current_time()
            date_spoken, date_display = get_current_date()
            
            spoken = f"{time_spoken}. {date_spoken}."
            display = f"{time_display}\n{date_display}"
            return spoken, display
            
        # Check for time query
        elif detect_time_intent(text):
            return get_current_time()
            
        # Check for date query
        elif detect_date_intent(text):
            return get_current_date()
            
        # Check for day query
        elif detect_day_intent(text):
            return get_current_day()
            
        # Check for calendar query
        elif detect_calendar_intent(text):
            return get_month_calendar()
            
        return None
        
    except Exception as e:
        logging.error(f"Error processing time query: {e}")
        return "I'm sorry, I encountered an error processing your request.", "Error processing request"

# =============================================================================
# Test Functions
# =============================================================================

def test_hybrid_detector():
    """Test the hybrid detector with sample audio."""
    test_audio = "data/audio/listen.wav"
    
    if not os.path.exists(test_audio):
        print(f"Test audio not found: {test_audio}")
        return
    
    print("="*60)
    print("HYBRID WAKE WORD DETECTOR TEST")
    print("="*60)
    
    detected, confidence, method = hybrid_wake_word_detection(test_audio, verbose=True)
    
    print("\n" + "="*60)
    print("RESULT:")
    print(f"  Detected: {'✅ YES' if detected else '❌ NO'}")
    print(f"  Confidence: {confidence:.2f}")
    print(f"  Method: {method}")
    print("="*60)

def test_time_queries():
    """Test the time/date query processor with sample queries."""
    test_queries = [
        "what time is it",
        "what's today's date",
        "what day is it",
        "tell me the time and date",
        "what's the calendar for this month"
    ]
    
    print("="*60)
    print("TIME/DATE QUERY PROCESSOR TEST")
    print("="*60)
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        result = process_time_query(query)
        if result:
            spoken, display = result
            print(f"Spoken: {spoken}")
            print(f"Display:\n{display}")
        else:
            print("Not a time/date query")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    # Run tests if this file is executed directly
    test_hybrid_detector()
    test_time_queries()
