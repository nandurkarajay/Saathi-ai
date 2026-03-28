import time
import sys
import random
import logging
from datetime import datetime

# Ensure project root is added to sys.path for absolute imports
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from core.voice_input import record_audio, transcribe_audio, ELDERLY_AUDIO_CONFIG
from core.chat_context import save_conversation, log_event, start_session, get_recent_context
from core.llm_gemma import query_gemma
from core.tts_output import speak_text, text_to_speech
from core.wake_detection import process_time_query
from core.task_system import start_scheduler
from core.reminder_system import process_reminder_request
from core.emergency_handler import check_and_handle_emergency
from core.music_player import handle_music, is_music_request, is_stop_request
from core.ui_styles import UI

# Import multi-language components
try:
    from core.language_support import get_language_manager, SupportedLanguage
    from core.multilang_voice_input import get_multilang_processor
    from core.multilang_llm import get_multilang_llm
    from core.multilang_tts import get_multilang_tts
    MULTI_LANGUAGE_ENABLED = True
except ImportError as e:
    MULTI_LANGUAGE_ENABLED = False
    logging.warning(f"Multi-language components not available: {e}")
    # Set up fallback values
    SupportedLanguage = None
    get_language_manager = None
    get_multilang_processor = None
    get_multilang_llm = None
    get_multilang_tts = None

# New reminder system is always available now
USING_NEW_REMINDER_SYSTEM = True

# Try to import hybrid detector, fallback to basic if not available
try:
    from core.hybrid_wake_detector import hybrid_wake_word_detection
    HYBRID_DETECTOR_AVAILABLE = True
except ImportError:
    HYBRID_DETECTOR_AVAILABLE = False
    logging.warning("Hybrid detector not available, using basic detection")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def get_time_appropriate_greeting():
    """Get greeting based on current time"""
    current_hour = datetime.now().hour
    
    if 5 <= current_hour < 12:
        return "Good morning! I'm Sathi, your helpful companion. How may I assist you?"
    elif 12 <= current_hour < 17:
        return "Good afternoon! I'm Sathi, here to help you. What can I do for you?"
    elif 17 <= current_hour < 22:
        return "Good evening! I'm Sathi, ready to assist you."
    else:
        return "Hello! I'm Sathi, your helpful companion. How may I assist you?"

# Multi-language greetings (will be overridden by language manager)
SATHI_GREETINGS = [
    "Hello! I'm Sathi, your helpful companion. How may I assist you?",
    "Good day! I'm here to help you. What can I do for you?",
    "Hello dear! I'm Sathi, ready to assist you.",
    "I'm here to help! Please tell me what you need.",
    "Yes, I'm listening! How can I make your day better?",
    "I'm your assistant Sathi. Please let me know how I can help you."
]

# Initialize multi-language components
if MULTI_LANGUAGE_ENABLED:
    language_manager = get_language_manager()
    voice_processor = get_multilang_processor()
    llm_processor = get_multilang_llm()
    tts_processor = get_multilang_tts()
else:
    language_manager = None
    voice_processor = None
    llm_processor = None
    tts_processor = None


def get_sleep_message(language_code):
    """Get sleep mode message in specified language"""
    if not MULTI_LANGUAGE_ENABLED or not SupportedLanguage:
        return "Okay, I'll be quiet now. Say Hey Sathi when you need me."
    
    messages = {
        SupportedLanguage.ENGLISH.value: "Okay, I'll be quiet now. Say Hey Sathi when you need me.",
        SupportedLanguage.HINDI.value: "ठीक है, मैं अब चुप हो जाऊंगा। जब जरूरत हो तो 'हे साथी' कहें।",
        SupportedLanguage.MARATHI.value: "ठीक आहे, मी अब शांत राहीन. जेव्हा गरज होताल तर 'हे साथी' म्हणा.",
        SupportedLanguage.GUJARATI.value: "બરાબર, હું હવે શાંત થઈ જઈશ. જયારે જરૂર હોય તો 'હે સાથી' કહો.",
        SupportedLanguage.TAMIL.value: "சரி, நான் இப்போல் அமைதானேன். தேவை வேண்டும் 'ஹே சாதி' சொல்லுங்கள்.",
        SupportedLanguage.TELUGU.value: "సరే, నేను ఇప్పుడు నిశబ్ధంగా ఉంటాను. అవసరం అవసరం 'హే సాథి' అనండి.",
        SupportedLanguage.BENGALI.value: "ঠিক আছি, আমি এখন চুপ থাকব। যখন প্রয়োজন হবে 'হে সাথী' বলুন।",
        SupportedLanguage.PUNJABI.value: "ਠੀਕ ਹੈ, ਮੈਂ ਹੁਣ ਚੁੱਪ ਰਹਾਂਗਾ। ਜਦੋਂ ਲੋੜ ਦੀ ਲੋੜ ਤਾਂ 'ਹੇ ਸਾਥੀ' ਕਹੋ।"
    }
    
    return messages.get(language_code, messages[SupportedLanguage.ENGLISH.value])

def get_farewell_message(language_code):
    """Get farewell message in specified language"""
    if not MULTI_LANGUAGE_ENABLED or not SupportedLanguage:
        return "Goodbye! Say 'Hey Sathi' anytime you need me."
    
    messages = {
        SupportedLanguage.ENGLISH.value: "Goodbye! Say 'Hey Sathi' anytime you need me.",
        SupportedLanguage.HINDI.value: "अलविदा! जब भी आपको मुझे चाहिए, 'हे साथी' कहें।",
        SupportedLanguage.MARATHI.value: "नमस्कार! जेव्हा तुम्हाला माझी गरज असेल, तेव्हा 'हे साथी' म्हणा.",
        SupportedLanguage.GUJARATI.value: "બાય! જ્યારે પણ તમને મારી જરૂર હોય, ત્યારે 'હે સાથી' કહો.",
        SupportedLanguage.TAMIL.value: "விடை! எப்போது வேண்டுமானாலும் 'ஹே சாதி' சொல்லுங்கள்.",
        SupportedLanguage.TELUGU.value: "వీడో! ఎప్పుడైనా అవసరం వస్తే 'హే సాథి' అనండి.",
        SupportedLanguage.BENGALI.value: "বিদায! যেকোনো সমযে 'হে সাথী' বলুন।",
        SupportedLanguage.PUNJABI.value: "ਵਿਦਾਇ! ਜਦੋਂ ਵੀ ਤੁਹਾਨੂੰ ਮੇਰੀ ਲੋੜ ਹੋਵੇ, 'ਹੇ ਸਾਥੀ' ਕਹੋ।"
    }
    
    return messages.get(language_code, messages[SupportedLanguage.ENGLISH.value])

# Import shared utilities
from core.utils import is_wake_word, WAKE_WORDS

def sathi_interaction(skip_wake_check=True, sleep_mode=False):
    """
    Records user's voice input → Transcribes → Gets Gemini response → Speaks output
    During conversation, wake word is NOT checked (skip_wake_check=True)
    In sleep mode, listens but doesn't respond until wake word is detected
    """
    UI.listening()

    # Step 1: Record user's voice input - VAD will stop when you stop speaking
    # Use temp file that will be deleted after transcription
    # Apply elderly-optimized settings
    audio_path = record_audio(
        duration=ELDERLY_AUDIO_CONFIG["max_duration"], 
        filename=None,  # None = temp file
        use_vad=True
    )

    if not audio_path:
        if not sleep_mode:
            UI.error("I couldn't hear you clearly. Please try again.")
        return None

    # Step 2: Transcribe with multi-language support
    if MULTI_LANGUAGE_ENABLED:
        transcription, detected_lang = voice_processor.transcribe_audio(
            audio_path, is_wake_word=skip_wake_check, target_language=None
        )
    else:
        # Fallback to original transcription
        transcription = transcribe_audio(audio_path, is_wake_word=False, delete_after=True)
        detected_lang = None
    
    if not transcription:
        if not sleep_mode:
            UI.error("Could not recognize speech.")
        return None

    UI.user_message(transcription)
    if detected_lang:
        config = language_manager.get_language_config(detected_lang)
        print(f"🌍 Language: {config.name} ({config.native_name})")
    
    # Check for emergency situations FIRST (highest priority)
    try:
        emergency_handled = check_and_handle_emergency(transcription)
        if emergency_handled:
            # Emergency was detected and handled - the emergency handler manages the response
            return detected_lang if MULTI_LANGUAGE_ENABLED and detected_lang else None
    except Exception as e:
        logging.error(f"Error in emergency handling: {e}")
        # Continue with normal flow even if emergency processing fails

    # Check for sleep command
    sleep_words = ['sleep', 'go to sleep', 'sleep mode', 'be quiet', 'quiet mode', 'stop talking']
    if any(word in transcription.lower() for word in sleep_words):
        UI.sleep_mode_header()
        
        # Speak sleep confirmation in detected language if available
        if MULTI_LANGUAGE_ENABLED and detected_lang:
            sleep_msg = get_sleep_message(detected_lang)
            tts_processor.speak_text(sleep_msg, detected_lang)
        else:
            speak_text("Okay, I'll be quiet now. Say Hey Sathi when you need me.")
        
        # Enter sleep mode loop
        while True:
            UI.sleep_listening()
            sleep_audio = record_audio(duration=10, filename=None)
            
            if not sleep_audio:
                time.sleep(0.5)
                continue
            
            sleep_transcription = transcribe_audio(sleep_audio, is_wake_word=True, delete_after=True)
            
            if sleep_transcription:
                # Check for wake word (multi-language support)
                if MULTI_LANGUAGE_ENABLED:
                    # Try multi-language wake word detection
                    transcribed, wake_lang = voice_processor.transcribe_audio(
                        sleep_audio, is_wake_word=True, target_language=None
                    )
                    if transcribed:
                        wake_words = language_manager.get_wake_words(wake_lang)
                        transcription_lower = transcribed.lower()
                        wake_detected = any(wake_word in transcription_lower for wake_word in wake_words)
                    else:
                        wake_detected = False
                else:
                    # Fallback to original wake word detection
                    wake_score = is_wake_word(sleep_transcription)
                    wake_detected = wake_score >= 0.6
                
                if wake_detected:
                    print(f"\n{'─' * 60}")
                    print("Wake Up - Sleep mode ended")
                    print(f"{'─' * 60}")
                    
                    # Wake up with cultural greeting
                    if MULTI_LANGUAGE_ENABLED and wake_lang:
                        greeting = language_manager.get_cultural_greeting(wake_lang)
                        print(f"Sathi: {greeting}")
                        tts_processor.speak_greeting(wake_lang)
                    else:
                        greeting = "I'm awake now! How can I help you?"
                        print(f"Sathi: {greeting}")
                        speak_text(greeting)
                    return  # Return to normal conversation
                else:
                    # In sleep mode, just listen, don't respond
                    print(f"Heard: '{sleep_transcription}' (still sleeping)")
        
        return
    
    # If in sleep mode, don't respond to anything except wake word
    if sleep_mode:
        return

    # Check for reminder/alarm requests FIRST (highest priority for elderly care)
    try:
        reminder_result = process_reminder_request(transcription)
        if reminder_result:
            spoken_text = reminder_result.spoken_text
            display_text = reminder_result.display_text
            reminder_data = reminder_result.reminder_data
            
            print("Reminder detected:")
            if reminder_data:
                print(f"   Task: {reminder_data['task']}")
                print(f"   Time: {reminder_data['time']}")
            
            # Speak the response in detected language
            if MULTI_LANGUAGE_ENABLED and detected_lang:
                tts_processor.speak_text(spoken_text, detected_lang)
            else:
                speak_text(spoken_text)
            print(f"Sathi: {display_text}")
            return detected_lang
    except Exception as e:
        logging.error(f"Error processing reminder: {e}")
        # Continue to normal processing if reminder fails

    # Check for stop music requests (high priority)
    try:
        if is_stop_request(transcription):
            print("Stop music request detected")
            
            # Create speak function for music player
            def music_speak(text):
                if MULTI_LANGUAGE_ENABLED and detected_lang:
                    tts_processor.speak_text(text, detected_lang)
                else:
                    speak_text(text)
            
            # Handle the stop music request
            music_handled = handle_music(transcription, music_speak)
            if music_handled:
                return detected_lang
    except Exception as e:
        logging.error(f"Error processing stop music request: {e}")

    # Check for music playback requests (high priority for elderly users)
    try:
        if is_music_request(transcription):
            print("Music request detected")
            
            # Create speak function for music player
            def music_speak(text):
                if MULTI_LANGUAGE_ENABLED and detected_lang:
                    tts_processor.speak_text(text, detected_lang)
                else:
                    speak_text(text)
            
            # Handle music request
            music_handled = handle_music(transcription, music_speak)
            if music_handled:
                return detected_lang
    except Exception as e:
        logging.error(f"Error processing music request: {e}")
        # Continue to normal processing if music fails

    # Check for time/date/calendar queries
    try:
        time_response = process_time_query(transcription)
        if time_response:
            spoken_text, display_text = time_response
            print(f"Sathi: {display_text}")
            
            # Speak time response in detected language
            if MULTI_LANGUAGE_ENABLED and detected_lang:
                tts_processor.speak_text(spoken_text, detected_lang)
            else:
                # Try primary speaking method first
                if not speak_text(spoken_text):
                    print("Primary TTS failed, trying backup method...")
                    # Try backup TTS method
                    if not text_to_speech(spoken_text):
                        print("Both TTS methods failed. Please check audio settings.")
                        print("Tip: Ensure Windows TTS voices are installed and audio is working")
            print(f"Sathi: {display_text}")
            return detected_lang
    except Exception as e:
        print("Error processing time query. Continuing with normal conversation.")
        logging.error(f"Error in time query processing: {str(e)}")

    # Check for quota status command
    quota_words = ['quota', 'requests left', 'how many requests', 'api status', 'gemini status']
    if any(word in transcription.lower() for word in quota_words):
        try:
            from core.api_quota_manager import print_quota_status, get_quota_details
            details = get_quota_details()
            
            quota_response = f"You have used {details['requests_made']} out of {details['daily_limit']} requests today. {details['remaining']} requests remaining."
            
            if MULTI_LANGUAGE_ENABLED and detected_lang:
                tts_processor.speak_text(quota_response, detected_lang)
            else:
                speak_text(quota_response)
            
            print(f"Sathi: {quota_response}")
            print_quota_status()
            return detected_lang
        except Exception as e:
            print(f"Error checking quota: {e}")
    
    # Check for exit commands
    exit_words = ['goodbye', 'bye', 'exit', 'stop', 'quit', 'end conversation']
    if any(word in transcription.lower() for word in exit_words):
        # Multi-language farewell
        if MULTI_LANGUAGE_ENABLED and detected_lang:
            farewell = get_farewell_message(detected_lang)
            print(f"Sathi: {farewell}")
            tts_processor.speak_text(farewell, detected_lang)
        else:
            farewell = "Goodbye! Say 'Hey Sathi' anytime you need me."
            print(f"Sathi: {farewell}")
            speak_text(farewell)
        print(f"\n{'─' * 60}")
        print("Conversation ended. Returning to wake word detection...")
        print(f"{'─' * 60}\n")
        # Restart the assistant to listen for wake word again
        sathi_assistant()
        return
    
    # If not a time query, process with LLM
    try:
        print("Processing...")
        
        if MULTI_LANGUAGE_ENABLED and detected_lang:
            # Use multi-language LLM
            context = get_recent_context(num_exchanges=5)
            response, response_lang = llm_processor.process_multilang_query(
                transcription, detected_lang, context
            )
            
            if response:
                print(f"Sathi: {response}")
                
                # Save conversation to context file
                save_conversation(transcription, response)
                
                # Speak response in appropriate language
                tts_processor.speak_text(response, response_lang)
                return response_lang
            else:
                print("I'm having trouble understanding. Could you please repeat?")
                tts_processor.speak_text("I'm having trouble understanding. Could you please repeat?", detected_lang)
                return detected_lang
        else:
            # Fallback to original LLM
            response = query_gemma(transcription)
            print(f"Sathi: {response}")
            
            # Save conversation to context file
            save_conversation(transcription, response)
            print("Context saved")
            
            # Speak the response
            speak_text(response)
            
    except Exception as e:
        print(f"LLM Error: {e}")
        return detected_lang

def sathi_assistant():
    """
    Starts task scheduler and initiates main conversation loop:
    Waits for wake word → Greets → Continuous conversation
    """
    # Start the task scheduler in background
    start_scheduler()
    logging.info("Task scheduler started - monitoring for reminders")
    
    # Start new chat session
    session_id = start_session()
    log_event("Sathi AI started")
    
    UI.welcome_message()

    # Step 1: Wait for wake word (VAD stops when you stop speaking)
    while True:
        # Use temp file for wake word detection with elderly-optimized settings
        audio_path = record_audio(
            duration=10,  # Shorter for wake word detection
            filename=None,
            use_vad=True
        )
        
        # Use hybrid detection if available, otherwise fallback to basic
        if HYBRID_DETECTOR_AVAILABLE:
            detected, score, method = hybrid_wake_word_detection(audio_path, verbose=False)
            
            if detected:
                print(f"Wake word detected! (Method: {method}, Score: {score:.2f})")
                greeting = get_time_appropriate_greeting()
                print(f"Sathi: {greeting}")
                speak_text(greeting)
                break
            else:
                print(f"Wake word not found (Score: {score:.2f}). Listening again...")
                time.sleep(0.5)
                continue
        
        # Fallback to basic detection - delete temp file after transcription
        transcription = transcribe_audio(audio_path, is_wake_word=True, delete_after=True)

        if not transcription:
            UI.status("No speech detected. Listening again...", "info")
            continue

        # Keep original transcription for matching  
        norm_trans = transcription.strip()
        print(f"Heard: {norm_trans}")

        # Get confidence score and use auto-accept threshold
        score = is_wake_word(norm_trans)
        print(f"Wake-word score: {score:.2f}")

        # Strong signal: accept immediately
        if score >= 0.85:
            UI.wake_word_detected()
            log_event(f"Wake word detected: '{norm_trans}' (score: {score:.2f})")
            greeting = get_time_appropriate_greeting()
            print(f"Sathi: {greeting}")
            speak_text(greeting)
            break
        # Good match: accept with lower threshold for "hey sathi"
        elif score >= 0.65:
            UI.wake_word_detected()
            log_event(f"Wake word detected: '{norm_trans}' (score: {score:.2f})")
            greeting = get_time_appropriate_greeting()
            print(f"Sathi: {greeting}")
            speak_text(greeting)
            break
        else:
            UI.status("Wake word not found. Listening again...", "info")
            time.sleep(0.5)

    # Step 2: Continuous conversation (NO wake word checking)
    UI.conversation_header()
    
    conversation_count = 0
    while True:
        conversation_count += 1
        UI.turn_indicator(conversation_count)
        
        # Record and process WITHOUT wake word checking
        sathi_interaction(skip_wake_check=True)
        
        # Brief pause for natural conversation flow
        time.sleep(0.3)  # Reduced from 1 second for faster response


if __name__ == "__main__":
    sathi_assistant()
