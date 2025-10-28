# ask_loop.py
"""
Monitor audio.wav -> run whisper-cli -> send transcript to Qwen (ollama) -> speak answer (pyttsx3).
Save this file in the root of your whisper.cpp project (so relative paths work).
"""
import sounddevice as sd
import numpy as np
import os
import time
import subprocess
import sys


# ----- CONFIG: needs to match तुमच्या फोल्डर/फाईल्स सोबत -----
WHISPER_CLI = r".\build\bin\Release\whisper-cli.exe"   # Windows path example
WHISPER_MODEL = r"models\ggml-small-q8_0.bin"
AUDIO_FILE = "audio.wav"
TXT_FILE = "audio.wav.txt"
POLL_INTERVAL = 1.0   # सेकंदांत तपासणी (कम करा -> अधिक sensitive, वाढवू शकता)
QWEN_MODEL_NAME = "qwen2.5"  # तुमच्या Ollama वर available model नाव ठेवा
# ---------------------------------------------------------

# optional conversation context (history)
CONTEXT = [
    {"role": "system", "content": "You are a helpful assistant."}
]

# try imports
try:
    from ollama import chat
except Exception as e:
    print("Missing python package 'ollama'. कृपया: pip install ollama")
    raise

try:
    import pyttsx3
except Exception as e:
    print("Missing python package 'pyttsx3'. कृपया: pip install pyttsx3")
    raise

engine = pyttsx3.init()

def run_whisper():
    """Run whisper-cli to transcribe audio.wav -> audio.wav.txt"""
    cmd = [
        WHISPER_CLI,
        "-m", WHISPER_MODEL,
        "-f", AUDIO_FILE,
        "-l", "en",
        "-nt", "-otxt"
    ]
    print("[1] Running Whisper CLI ...")
    subprocess.run(cmd, check=True)
    print("[1] Whisper finished.")

def read_transcript():
    """Return trimmed text from audio.wav.txt"""
    if not os.path.exists(TXT_FILE):
        return ""
    with open(TXT_FILE, "r", encoding="utf-8") as f:
        return f.read().strip()

def ask_qwen(question):
    """Send question to Qwen via ollama.chat and return answer text"""
    messages = CONTEXT.copy()
    messages.append({"role": "user", "content": question})
    print("[2] Sending to Qwen...")
    resp = chat(model=QWEN_MODEL_NAME, messages=messages, stream=False)
    # try common extraction
    if isinstance(resp, dict):
        return resp.get("message", {}).get("content", str(resp))
    else:
        # fallback
        try:
            return resp.message.get("content", str(resp))
        except Exception:
            return str(resp)

def speak_text(text):
    """Speak answer using pyttsx3 (offline)"""
    print("[3] Speaking answer...")
    engine.say(text)
    engine.runAndWait()

def main():
    print("=== Whisper -> Qwen loop starting ===")
    print("Ensure: 'ollama serve' is running in another terminal (so model isn't reloaded each time).")
    if not os.path.exists(WHISPER_CLI):
        print(f"Warning: whisper-cli not found at {WHISPER_CLI}. Edit WHISPER_CLI path in script.")
    if not os.path.exists(WHISPER_MODEL):
        print(f"Warning: whisper model not found at {WHISPER_MODEL}. Edit WHISPER_MODEL path in script.")
    last_mtime = 0
    last_question = None

    # If audio file exists, record its current mtime
    if os.path.exists(AUDIO_FILE):
        last_mtime = os.path.getmtime(AUDIO_FILE)

    try:
        while True:
            try:
                if os.path.exists(AUDIO_FILE):
                    m = os.path.getmtime(AUDIO_FILE)
                    if m != last_mtime:
                        # new/changed audio detected
                        last_mtime = m
                        # small wait so file write completes
                        time.sleep(0.5)
                        run_whisper()
                        q = read_transcript()
                        if not q:
                            print("No transcript produced.")
                            continue
                        if q == last_question:
                            print("Same question as previous — skipping.")
                            continue
                        print("Question:", q)
                        last_question = q
                        ans = ask_qwen(q)
                        print("Answer:\n", ans)
                        speak_text(ans)
                time.sleep(POLL_INTERVAL)
            except subprocess.CalledProcessError as e:
                print("Error running whisper-cli:", e)
                time.sleep(2)
            except Exception as e:
                print("Unexpected error:", e)
                time.sleep(2)
    except KeyboardInterrupt:
        print("Exiting loop. Bye.")
        sys.exit(0)

if __name__ == "__main__":
    main()
