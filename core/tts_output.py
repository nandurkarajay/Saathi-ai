import pyttsx3
import os
from datetime import datetime

def text_to_speech(text, output_dir="data/audio"):
    """
    Convert text to speech and save as audio file
    Args:
        text (str): Text to convert to speech
        output_dir (str): Directory to save audio file
    """
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Initialize TTS engine
        engine = pyttsx3.init()
        
        # Set properties
        engine.setProperty('rate', 120)  # slower for elderly
        engine.setProperty('volume', 0.9)  # Volume level (0.0 to 1.0)
        
        # Use system default voice (Ravi if set as default in Windows)
        # The system default will be used automatically
        voices = engine.getProperty('voices')
        print(f"🔊 Using voice: {voices[0].name if voices else 'Default'}")
        
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

def speak_text(text):
    """
    Speak text directly without saving to file
    Args:
        text (str): Text to speak
    """
    if not text:
        print("❌ TTS Error: Empty text provided")
        return
        
    try:
        engine = pyttsx3.init()
        
        # Configure voice properties for elderly users
        engine.setProperty('rate', 150)     # Speed - slightly slower
        engine.setProperty('volume', 0.9)   # Volume - clear but not too loud
        
        # Use system default voice (Ravi if set as default in Windows)
        voices = engine.getProperty('voices')
        if not voices:
            print("⚠️ No TTS voices found. Please check system TTS settings.")
            return
            
        print(f"🔊 Using voice: {voices[0].name if voices else 'Default'}")
        
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
