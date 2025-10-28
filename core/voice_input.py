import sounddevice as sd
from scipy.io.wavfile import write
import subprocess
import os

# 🧠 Step 1: Record voice from mic
def record_audio(duration=8, filename="data/audio/audio.wav"):
    """Record audio from the default microphone with clear visual feedback.

    Returns the path to the saved WAV file on success, or None on failure
    (including user interrupt via Ctrl-C).
    """
    print("\n" + "="*50)
    print("Ready to Listen!")
    print("="*50)

    # Ensure parent directory exists
    parent = os.path.abspath(os.path.dirname(filename))
    if parent and not os.path.exists(parent):
        os.makedirs(parent, exist_ok=True)

    fs = 16000  # Sample rate (16 kHz)

    try:
        audio = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
        sd.wait()  # Wait until recording finishes
    except KeyboardInterrupt:
        # User interrupted recording (Ctrl-C). Stop the stream and return None.
        try:
            sd.stop()
        except Exception:
            pass
        print("Recording interrupted by user.")
        return None
    except Exception as e:
        print(f"Recording failed: {e}")
        return None

    try:
        write(filename, fs, audio)  # Save file
        print(f"Recording complete. Saved as {filename}")
        return filename
    except Exception as e:
        print(f"Failed to save recording: {e}")
        return None


# 🧠 Step 2: Transcribe using Whisper.cpp
def transcribe_audio(audio_path):
    whisper_exe = "whisper.cpp/build/bin/Release/whisper-cli.exe"  # Updated to use whisper-cli.exe
    model_path = "models/ggml-small-q8_0.bin"

    # Check if paths exist
    if not os.path.exists(whisper_exe):
        print("Whisper executable not found! Check build path.")
        return None
    if not os.path.exists(model_path):
        print("Model file not found! Place model in models/ folder.")
        return None

    print("Transcribing using Whisper.cpp...")
    command = [whisper_exe, "-m", model_path, "-f", audio_path, "--language", "en"]
    
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=60)
        
        # Check for errors
        if result.returncode != 0:
            print(f"Transcription failed with return code: {result.returncode}")
            print(f"Error output: {result.stderr}")
            return None
            
        # Extract transcribed text from the output
        output = result.stdout
        print(f"Raw whisper output: {output}")
        
        # Look for the transcribed text in the output
        lines = output.split('\n')
        transcribed_text = ""
        
        for line in lines:
            if '-->' in line and ']' in line:
                # Extract text after the timestamp
                if ']' in line:
                    text_part = line.split(']')[-1].strip()
                    if text_part:
                        transcribed_text += text_part + " "
        
        if not transcribed_text.strip():
            # Fallback: look for any text in the output
            for line in lines:
                if line.strip() and not line.startswith('whisper_') and not line.startswith('system_info:') and not line.startswith('main:') and not line.startswith('['):
                    transcribed_text += line.strip() + " "

        transcribed_text = transcribed_text.strip()
        
        if transcribed_text:
            print(f"\n Transcribed Text: {transcribed_text}")
            return transcribed_text
        else:
            print(" No transcribed text found in output")
            return None
            
    except subprocess.TimeoutExpired:
        print("Transcription timed out")
        return None
    except Exception as e:
        print(f"Transcription failed with error: {e}")
        return None


# 🧠 Step 3: Save transcription to file
def save_transcription_to_file(transcription, output_file="data/audio/audio.txt"):
    """Save the transcribed text to a file (default: data/audio/audio.txt)

    This path matches what `core/main.py` expects so the full STT -> LLM -> TTS
    flow can read the transcription automatically.
    """
    try:
        # Ensure folder exists
        parent = os.path.abspath(os.path.dirname(output_file))
        if parent and not os.path.exists(parent):
            os.makedirs(parent, exist_ok=True)

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(transcription)
        print(f"Transcription saved to {output_file}")
    except Exception as e:
        print(f"Failed to save transcription: {e}")

# 🧠 Step 4: Main flow
def main():
    audio_path = record_audio(duration=5)
    transcription = transcribe_audio(audio_path)
    
    if transcription:
        save_transcription_to_file(transcription)
    else:
        print(" No transcription to save")


if __name__ == "__main__":
    main()
