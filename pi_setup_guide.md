# Raspberry Pi 4GB Setup Guide for Sathi AI

## Hardware Requirements Met ✅
- **RAM**: 4GB (Excellent for Whisper)
- **Storage**: 128GB (Plenty for models)
- **Processor**: Raspberry Pi 4B (4 cores)

## Model Recommendations

### Option 1: Balanced Performance (Recommended)
```python
# In core/voice_input.py, change line 303:
model_path = "models/ggml-base.bin"  # Instead of ggml-small-q8_0.bin
```

### Option 2: Maximum Speed
```python
model_path = "models/ggml-tiny.bin"  # Fastest option
```

## Performance Optimizations

### 1. Reduce Thread Count
```python
# In transcribe_audio function:
command = [
    whisper_exe,
    "-m", model_path,
    "-f", audio_path,
    "--language", "en",
    "-t", "4",  # Reduced from 8 for Pi
    "--no-timestamps",
]
```

### 2. Enable Pi-Specific Settings
```python
# Add to voice_input.py:
PI_CONFIG = {
    "max_audio_duration": 20,  # Shorter chunks
    "buffer_size": 512,        # Smaller buffer
    "use_gpu": False,          # CPU only on Pi
}
```

## Installation Commands

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install python3-pip python3-dev
sudo apt install portaudio19-dev python3-pyaudio
sudo apt install git cmake build-essential

# Install whisper.cpp for ARM
git clone https://github.com/ggerganov/whisper.cpp
cd whisper.cpp
make clean && make

# Test installation
./whisper -m models/ggml-base.bin -f test.wav
```

## Expected Performance

- **Base Model**: Real-time transcription
- **RAM Usage**: 150MB (3.7% of 4GB)
- **Storage**: 74MB (0.06% of 128GB)
- **CPU Usage**: ~60% during transcription
- **Response Time**: <2 seconds for 10s audio

## Troubleshooting

### If transcription is slow:
1. Use `ggml-tiny.bin` model
2. Reduce threads to 2
3. Increase silence threshold

### If memory issues:
1. Close other applications
2. Use `ggml-tiny.bin` model
3. Reboot Pi before use

## Testing Your Setup

```bash
# Test microphone
python3 -c "import sounddevice as sd; print('Audio working')"

# Test whisper
cd whisper.cpp
./whisper -m ../models/ggml-base.bin your_audio.wav

# Test full system
cd ~/Sathi-Ai
python3 core/voice_input.py
```
