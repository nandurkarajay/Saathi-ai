import pyttsx3
import os
from datetime import datetime

def text_to_speech(text, output_dir="data/audio", use_male_voice=False):
    """
    Convert text to speech and save as audio file
    Args:
        text (str): Text to convert to speech
        output_dir (str): Directory to save audio file
        use_male_voice (bool): If True, uses male voice; if False, uses female voice
    """
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Initialize TTS engine
        engine = pyttsx3.init()
        
        # Set properties
        engine.setProperty('rate', 120)  # slower for elderly
        engine.setProperty('volume', 0.9)  # Volume level (0.0 to 1.0)
        
        # Get available voices
        voices = engine.getProperty('voices')
        
        # Select voice based on preference
        selected_voice = None
        for voice in voices:
            voice_name = voice.name.lower()
            if use_male_voice:
                if 'david' in voice_name or 'male' in voice_name:
                    selected_voice = voice.id
                    break
            else:
                if 'zira' in voice_name or 'female' in voice_name:
                    selected_voice = voice.id
                    break
        
        # If preferred voice type not found, use the first available voice
        if selected_voice:
            engine.setProperty('voice', selected_voice)
        elif voices:
            engine.setProperty('voice', voices[0].id)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(output_dir, f"response_{timestamp}.wav")
        
        # Save to file
        engine.save_to_file(text, output_file)
        engine.runAndWait()
        
        print(f"🔊 Audio response saved: {output_file}")
        return output_file
        
    except Exception as e:
        print(f"❌ TTS Error: {e}")
        return None

def speak_text(text, use_male_voice=False):
    """
    Speak text directly without saving to file
    Args:
        text (str): Text to speak
        use_male_voice (bool): If True, uses male voice; if False, uses female voice
    """
    if not text:
        print("❌ TTS Error: Empty text provided")
        return
        
    try:
        engine = pyttsx3.init()
        
        # Configure voice properties for elderly users
        engine.setProperty('rate', 150)     # Speed - slightly slower
        engine.setProperty('volume', 0.9)   # Volume - clear but not too loud
        
        # Get available voices
        voices = engine.getProperty('voices')
        if not voices:
            print("⚠️ No TTS voices found. Please check system TTS settings.")
            return
            
        # Select voice based on preference
        selected_voice = None
        for voice in voices:
            voice_name = voice.name.lower()
            if use_male_voice and ('david' in voice_name or 'male' in voice_name):
                selected_voice = voice.id
                break
            elif not use_male_voice and ('zira' in voice_name or 'female' in voice_name):
                selected_voice = voice.id
                break
        
        # If preferred voice not found, use first available
        if selected_voice:
            engine.setProperty('voice', selected_voice)
        else:
            engine.setProperty('voice', voices[0].id)
            print("⚠️ Preferred voice not found, using default voice")
        
        print(f"🔊 Speaking: {text}")
        engine.say(text)
        engine.runAndWait()
        return True
        
    except Exception as e:
        print(f"❌ TTS Error: {str(e)}")
        print("💡 Tip: Make sure your system's audio is working and TTS voices are installed")
        return False

if __name__ == "__main__":
    # Test TTS
    test_text = "Hello, this is a test of the text to speech system."
    print("Testing TTS...")
    output_file = text_to_speech(test_text)
    if output_file:
        print(f"✅ Test audio saved: {output_file}")
    else:
        print("❌ TTS test failed")
