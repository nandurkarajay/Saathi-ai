"""
Voice Input Module for Sathi AI
Optimized for elderly users with sensitive audio detection
"""

import sounddevice as sd
from scipy.io.wavfile import write
import subprocess
import os
import numpy as np
import tempfile


# Elderly-optimized audio settings
ELDERLY_AUDIO_CONFIG = {
    "silence_threshold": 200,      # Low threshold for soft voices
    "silence_duration": 1.5,       # Quick response for elderly users
    "max_duration": 15,             # Shorter recording windows
    "min_speech_duration": 0.5,    # Minimum speech required
    "noise_floor_multiplier": 1.8, # Sensitive adaptive threshold
    "calibration_chunks": 3        # Quick noise calibration
}

# 🧠 Step 1: Record voice from mic with Voice Activity Detection
def record_audio_with_vad(filename=None, 
                          silence_threshold=None,
                          silence_duration=None, 
                          max_duration=None,
                          return_array=False,
                          noise_reduction=True,
                          min_speech_duration=None):
    """
    Record audio until user stops speaking (Voice Activity Detection).
    Optimized for elderly users with sensitive detection.
    
    Args:
        filename: Where to save the audio (if None, returns temp file or array)
        silence_threshold: Energy threshold to detect speech (uses elderly config if None)
        silence_duration: Seconds of silence before stopping (uses elderly config if None)
        max_duration: Maximum recording duration in seconds (uses elderly config if None)
        return_array: If True, returns numpy array instead of file path
        noise_reduction: If True, applies noise reduction
        min_speech_duration: Minimum speech duration required (uses elderly config if None)
    
    Returns:
        Path to saved WAV file, numpy array, or None on failure
    """
    config = ELDERLY_AUDIO_CONFIG
    silence_threshold = silence_threshold or config["silence_threshold"]
    silence_duration = silence_duration or config["silence_duration"]
    max_duration = max_duration or config["max_duration"]
    min_speech_duration = min_speech_duration or config["min_speech_duration"]
    calibration_chunks = config["calibration_chunks"]
    noise_floor_multiplier = config["noise_floor_multiplier"]
    
    print("\n" + "="*50)
    print("🎤 Speak now... (will stop when you finish)")
    print("="*50)
    
    fs = 16000  # Sample rate
    chunk_duration = 0.1  # 100ms chunks
    chunk_samples = int(fs * chunk_duration)
    
    recorded_chunks = []
    silent_chunks = 0
    speech_chunks = 0
    silence_chunks_needed = int(silence_duration / chunk_duration)
    speech_detected = False
    
    # Noise floor estimation
    noise_floor = 0
    
    try:
        import time
        
        with sd.InputStream(samplerate=fs, channels=1, dtype='int16') as stream:
            print("🎧 Adjusting to your voice...")
            start_time = time.time()
            chunk_count = 0
            noise_samples = []
            
            while True:
                # Read audio chunk
                chunk, overflowed = stream.read(chunk_samples)
                chunk_count += 1
                
                # Calculate energy (volume) of chunk
                energy = np.sqrt(np.mean(chunk.astype(float) ** 2))
                
                # Calibrate noise floor (first few chunks)
                if chunk_count <= calibration_chunks:
                    noise_samples.append(energy)
                    if chunk_count == calibration_chunks:
                        noise_floor = np.mean(noise_samples)
                        # Adaptive threshold: noise floor + margin
                        adaptive_threshold = max(silence_threshold, noise_floor * noise_floor_multiplier)
                        print(f"🔇 Noise floor: {noise_floor:.0f}, Threshold: {adaptive_threshold:.0f}")
                    continue
                
                # Use adaptive threshold if available
                current_threshold = adaptive_threshold if chunk_count > calibration_chunks else silence_threshold
                
                # Check if speech is present (above threshold)
                if energy > current_threshold:
                    if not speech_detected:
                        print("🗣️ Speech detected, recording...")
                        speech_detected = True
                    recorded_chunks.append(chunk)
                    speech_chunks += 1
                    silent_chunks = 0
                else:
                    # Silence detected
                    if speech_detected:
                        recorded_chunks.append(chunk)
                        silent_chunks += 1
                        
                        # Stop if enough silence after speech
                        if silent_chunks >= silence_chunks_needed:
                            elapsed = time.time() - start_time
                            # Check if we had enough speech
                            speech_duration = speech_chunks * chunk_duration
                            if speech_duration >= min_speech_duration:
                                print(f"✅ Recording complete ({elapsed:.1f}s)")
                                break
                            else:
                                print("⚠️ Speech too short, continuing...")
                                silent_chunks = 0
                                speech_detected = False
                
                # Check max duration
                elapsed = time.time() - start_time
                if elapsed > max_duration:
                    print(f"⏱️ Max duration reached ({max_duration}s)")
                    # Check if we had enough speech
                    speech_duration = speech_chunks * chunk_duration
                    if speech_duration >= min_speech_duration:
                        break
                    else:
                        print("⚠️ Not enough speech detected, please try again")
                        return None
        
        # Combine all chunks
        if recorded_chunks and speech_detected:
            audio = np.concatenate(recorded_chunks, axis=0)
            
            # Apply noise reduction if enabled
            if noise_reduction and noise_floor > 0:
                # Simple noise gate: reduce audio below threshold
                audio_float = audio.astype(float)
                audio_energy = np.abs(audio_float)
                
                # Create noise gate mask
                gate_threshold = noise_floor * 1.5
                mask = audio_energy > gate_threshold
                
                # Apply gate with smooth transition
                audio_float = audio_float * mask
                audio = audio_float.astype('int16')
                print(f"🔇 Noise reduction applied")
            
            # Return array if requested (no file saved)
            if return_array:
                print(f"✅ Audio captured ({len(audio)} samples)")
                return audio
            
            # Create temp file if no filename provided
            if filename is None:
                temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
                filename = temp_file.name
                temp_file.close()
                print(f"💾 Using temporary file")
            
            write(filename, fs, audio)
            return filename
        else:
            print("❌ No clear speech detected")
            print("💡 Please speak clearly and a bit louder")
            return None
            
    except KeyboardInterrupt:
        print("\n⚠️ Recording interrupted")
        return None
    except Exception as e:
        print(f"❌ Recording failed: {e}")
        return None


def record_audio(duration=15, filename="data/audio/audio.wav", use_vad=True):
    """
    Record audio from the default microphone.
    Uses elderly-optimized settings by default.
    
    Args:
        duration: Maximum duration (only used if use_vad=False)
        filename: Where to save the audio
        use_vad: If True, uses Voice Activity Detection (stops when user stops speaking)
                 If False, uses fixed duration
    
    Returns the path to the saved WAV file on success, or None on failure
    """
    # Use VAD by default for natural interaction
    if use_vad:
        return record_audio_with_vad(filename=filename, max_duration=duration)
    
    # Original fixed duration recording
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


def test_microphone_sensitivity():
    """
    Test microphone sensitivity and provide feedback for elderly users
    """
    print("="*60)
    print("🎤 MICROPHONE SENSITIVITY TEST")
    print("="*60)
    print("Please speak normally for 3 seconds...")
    
    fs = 16000
    duration = 3
    chunk_duration = 0.1
    chunk_samples = int(fs * chunk_duration)
    
    try:
        with sd.InputStream(samplerate=fs, channels=1, dtype='int16') as stream:
            print("🎧 Recording...")
            energies = []
            
            for i in range(int(duration / chunk_duration)):
                chunk, _ = stream.read(chunk_samples)
                energy = np.sqrt(np.mean(chunk.astype(float) ** 2))
                energies.append(energy)
            
            avg_energy = np.mean(energies)
            max_energy = np.max(energies)
            min_energy = np.min(energies)
            
            print(f"\n📊 Microphone Analysis:")
            print(f"   Average energy: {avg_energy:.0f}")
            print(f"   Peak energy: {max_energy:.0f}")
            print(f"   Noise floor: {min_energy:.0f}")
            
            # Recommendations for elderly users
            if avg_energy < 100:
                print("⚠️  Your voice is quite quiet")
                print("💡 Try speaking louder or closer to the microphone")
            elif avg_energy > 2000:
                print("⚠️  Your voice is very loud")
                print("💡 Try speaking a bit softer")
            else:
                print("✅ Your voice level is perfect!")
            
            # Suggest optimal threshold based on voice
            suggested_threshold = max(150, avg_energy * 0.3)
            print(f"💡 Optimal threshold for your voice: {suggested_threshold:.0f}")
            
            # Compare with elderly config
            config_threshold = ELDERLY_AUDIO_CONFIG["silence_threshold"]
            if suggested_threshold > config_threshold:
                print(f"🔧 Your voice needs a higher threshold ({suggested_threshold:.0f} > {config_threshold})")
            else:
                print(f"✅ Current settings work well for your voice")
            
    except Exception as e:
        print(f"❌ Microphone test failed: {e}")
        print("💡 Please check your microphone is connected and not muted")


# 🧠 Step 2: Transcribe using Whisper.cpp
def transcribe_audio(audio_path, is_wake_word=False, delete_after=False):
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
    
    # Build command with optimized parameters for speed
    command = [
        whisper_exe, 
        "-m", model_path, 
        "-f", audio_path, 
        "--language", "en",
        "-t", "8",  # Use 8 threads for maximum speed
        "--no-timestamps",  # Skip timestamps for faster processing
    ]
    
    # Add prompt for wake word detection to guide Whisper
    if is_wake_word:
        command.extend(["--prompt", "Hey Sathi, Hi Sathi, Hello Sathi"])
        command.append("--translate")  # Only translate during wake word detection
    
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
        
        # Filter out foreign language indicators
        if transcribed_text and "speaking in foreign language" in transcribed_text.lower():
            print("⚠️ Foreign language detected, attempting alternative recognition...")
            # Try to extract any English words that might be present
            transcribed_text = None
        
        if transcribed_text:
            print(f"\n✅ Transcribed Text: {transcribed_text}")
            
            # Delete temp file if requested
            if delete_after and audio_path:
                try:
                    os.unlink(audio_path)
                    print(f"🗑️ Deleted temporary audio file")
                except:
                    pass
            
            return transcribed_text
        else:
            print("❌ No transcribed text found in output")
            
            # Delete temp file even on failure
            if delete_after and audio_path:
                try:
                    os.unlink(audio_path)
                except:
                    pass
            
            return None
            
    except subprocess.TimeoutExpired:
        print("Transcription timed out")
        if delete_after and audio_path:
            try:
                os.unlink(audio_path)
            except:
                pass
        return None
    except Exception as e:
        print(f"Transcription failed with error: {e}")
        if delete_after and audio_path:
            try:
                os.unlink(audio_path)
            except:
                pass
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

# 🧠 Step 4: Main test function
def main():
    """
    Test the elderly-optimized voice input system
    """
    print("="*60)
    print("🎤 ELDERLY-OPTIMIZED VOICE INPUT TEST")
    print("="*60)
    
    # Test microphone sensitivity first
    test_microphone_sensitivity()
    
    print("\n" + "="*60)
    print("🎤 TESTING VOICE RECORDING")
    print("="*60)
    
    # Test optimized recording
    audio_path = record_audio_with_vad(filename="data/audio/test_elderly.wav")
    transcription = transcribe_audio(audio_path)
    
    if transcription:
        save_transcription_to_file(transcription)
        print(f"✅ Success! Transcription: '{transcription}'")
    else:
        print("❌ No transcription received")
    
    print("\n" + "="*60)
    print("🎯 ELDERLY OPTIMIZATION SUMMARY:")
    print("="*60)
    config = ELDERLY_AUDIO_CONFIG
    print(f"✅ Silence Threshold: {config['silence_threshold']} (sensitive to soft voices)")
    print(f"✅ Silence Duration: {config['silence_duration']}s (quick response)")
    print(f"✅ Max Duration: {config['max_duration']}s (elderly-friendly)")
    print(f"✅ Min Speech Duration: {config['min_speech_duration']}s (prevents false starts)")
    print(f"✅ Noise Floor Multiplier: {config['noise_floor_multiplier']}x (adaptive)")
    print(f"✅ Calibration Chunks: {config['calibration_chunks']} (fast setup)")
    print("="*60)


if __name__ == "__main__":
    main()
