import time
import os
import sys
import re
from pathlib import Path
from difflib import SequenceMatcher
import random

# Ensure project root is added to sys.path for absolute imports
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from core.voice_input import record_audio
from core.voice_input import transcribe_audio
from core.llm_gemma import query_gemma
from core.tts_output import speak_text, text_to_speech
from core.calendar_and_clock import process_time_query
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Define wake words
WAKE_WORDS = [
    "hey sathi", "hi sathi", "ok sathi", "sathi",
    "hello sathi", "dear sathi", "sathi please",
    "sathi help", "listen sathi", "sathi are you there"
]

# Warm and friendly greetings for elderly users
SATHI_GREETINGS = [
    "Hello! I'm Sathi, your helpful companion. How may I assist you?",
    "Good day! I'm here to help you. What can I do for you?",
    "Hello dear! I'm Sathi, ready to assist you.",
    "I'm here to help! Please tell me what you need.",
    "Yes, I'm listening! How can I make your day better?",
    "I'm your assistant Sathi. Please let me know how I can help you."
]

def is_wake_word(text, span_threshold=0.65, token_threshold=0.85):
    """
    Improved wake-word scoring.

    Returns a float score between 0.0 and 1.0 indicating how closely the
    given `text` matches any of the `WAKE_WORDS`.

    Matching strategy:
    - normalize text (lowercase, remove punctuation)
    - exact match or substring -> high score
    - token-subset match -> high score
    - sliding window token comparisons using SequenceMatcher -> span_threshold
    - single-token fuzzy matches (e.g. "sathi" vs "sathy") -> token_threshold

    This returns the best score found. Callers should decide cutoffs.
    """
    if not text:
        return 0.0

    # Normalize incoming text
    norm = re.sub(r'[^a-z0-9 ]', ' ', text.lower())
    norm = re.sub(r'\s+', ' ', norm).strip()
    tokens = norm.split()

    best_score = 0.0

    for wake in WAKE_WORDS:
        w = re.sub(r'[^a-z0-9 ]', ' ', wake.lower()).strip()
        w = re.sub(r'\s+', ' ', w)
        if not w:
            continue

        # exact full-string match
        if norm == w:
            return 1.0

        # substring match -> strong signal
        if w in norm:
            return 0.95

        w_tokens = w.split()

        # token-subset (all wake tokens present somewhere)
        if all(t in tokens for t in w_tokens):
            return 0.9

        # sliding window over tokens for phrase-level fuzzy match
        win_len = max(1, len(w_tokens))
        for i in range(0, max(1, len(tokens) - win_len + 1)):
            window = ' '.join(tokens[i:i + win_len])
            score = SequenceMatcher(None, window, w).ratio()
            if score > best_score:
                best_score = score
            if score >= span_threshold:
                return score

        # single-token fuzzy match (helps when transcription mangles one word)
        for wt in w_tokens:
            for tk in tokens:
                s = SequenceMatcher(None, tk, wt).ratio()
                if s > best_score:
                    best_score = s
                if s >= token_threshold:
                    return s

    return best_score

def sathi_interaction():
    """
    Records user's voice input → Transcribes → Gets Gemini response → Speaks output
    """
    print("\n Sathi: I'm listening...")

    # Step 1: Record user's voice input with better duration for elderly users
    audio_path = record_audio(duration=8)  # Increased duration for slower speech

    if not audio_path:
        print("\n❌ I couldn't hear you clearly. Please try again.")
        print("💡 Tip: Speak a little louder and closer to the microphone")
        return

    # Step 2: Transcribe
    transcription = transcribe_audio(audio_path)
    if not transcription:
        print("❌ Could not recognize speech.")
        return

    print(f"🗣️ You said: {transcription}")

    # Check for time/date/calendar queries first
    try:
        time_response = process_time_query(transcription)
        if time_response:
            spoken_text, display_text = time_response
            print(f"💬 Sathi: {display_text}")
            
            # Ensure we have valid text to speak
            if spoken_text and isinstance(spoken_text, str):
                # Try primary speaking method first
                if not speak_text(spoken_text, use_male_voice=True):
                    print("⚠️ Primary TTS failed, trying backup method...")
                    # Try backup TTS method
                    if not text_to_speech(spoken_text, use_male_voice=True):
                        print("❌ Both TTS methods failed. Please check audio settings.")
                        print("💡 Tip: Ensure Windows TTS voices are installed and audio is working")
            else:
                print("⚠️ Invalid response format from time query")
                speak_text("I'm having trouble telling the time right now.", use_male_voice=True)
            return
    except Exception as e:
        print("⚠️ Error processing time query. Continuing with normal conversation.")
        logging.error(f"Error in time query processing: {str(e)}")

    # If not a time query, process with LLM
    try:
        print("🧠 Thinking...")
        response = query_gemma(transcription)
        print(f"💬 Sathi: {response}")
    except Exception as e:
        print(f"⚠️ LLM Error: {e}")
        return

    # Step 4: Speak response with male voice
    speak_text(response, use_male_voice=True)
    text_to_speech(response, use_male_voice=True)

def sathi_assistant():
    """
    Waits for wake word → Greets → Continuous conversation
    """
    print("Sathi AI is running!")
    print(" Say 'Hey Sathi' to wake me up...\n")

    # Step 1: Wait for wake word
    while True:
        audio_path = record_audio(duration=5, filename="data/audio/listen.wav")
        transcription = transcribe_audio(audio_path)

        if not transcription:
            print("No speech detected. Listening again...\n")
            continue

        # Keep original transcription for matching  
        norm_trans = transcription.strip()
        print(f"Heard: {norm_trans}")

        # Get confidence score and use auto-accept threshold
        score = is_wake_word(norm_trans)
        print(f"Wake-word score: {score:.2f}")

        if score >= 0.70:  # More permissive threshold for elderly users
            print("Wake word detected!")
            greeting = random.choice(SATHI_GREETINGS)
            print(f"Sathi: {greeting}")
            speak_text(greeting, use_male_voice=True)
            text_to_speech(greeting, use_male_voice=True)
            break
        else:
            print("Wake word not found. Listening again...\n")
            time.sleep(0.8)
            continue

        # Keep original transcription for fuzzy matching (more info)
        norm_trans = transcription.strip()
        print(f"Heard: {norm_trans}")

        # Get a confidence score (0.0 - 1.0)
        score = is_wake_word(norm_trans)
        print(f"Wake-word score: {score:.2f}")

        # Strong signal: accept immediately
        if score >= 0.9:
            print(" Wake word detected (confident)!")

            # Pick a random warm greeting
            greeting = random.choice(SATHI_GREETINGS)
            print(f"Sathi: {greeting}")
            speak_text(greeting, use_male_voice=True)
            text_to_speech(greeting, use_male_voice=True)

            # Start conversation directly (no extra “yes sir” pause)
            break
        # Borderline: ask for a quick confirmation (helps reduce misses)
        elif score >= 0.55:
            print("Wake word borderline — asking for confirmation...")
            # Ask a short spoken confirmation
            confirm_prompt = "Did you say Sathi? Please say yes or no."
            speak_text(confirm_prompt, use_male_voice=True)
            text_to_speech(confirm_prompt, use_male_voice=True)

            # Short re-listen
            confirm_audio = record_audio(duration=3, filename="data/audio/confirm.wav")
            confirm_trans = transcribe_audio(confirm_audio) if confirm_audio else None
            if confirm_trans:
                ct = confirm_trans.lower()
                print(f"Confirmation heard: {ct}")
                if any(w in ct for w in ("yes", "yeah", "yup", "ya", "correct", "right")):
                    print("User confirmed wake word.")
                    greeting = random.choice(SATHI_GREETINGS)
                    print(f"Sathi: {greeting}")
                    speak_text(greeting, use_male_voice=True)
                    text_to_speech(greeting, use_male_voice=True)
                    break
                else:
                    print("Confirmation negative — continuing to listen...\n")
                    time.sleep(0.5)
                    continue
            else:
                print("No confirmation heard — continuing to listen...\n")
                time.sleep(0.5)
                continue

        else:
            print("Wake word not found. Listening again...\n")
            time.sleep(1)

    # Step 2: Continuous conversation
    while True:
        sathi_interaction()
        print("\n Listening for your next question...\n")
        time.sleep(1)


if __name__ == "__main__":
    sathi_assistant()
