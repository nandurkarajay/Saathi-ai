# Sathi-AI: Elderly Companionship & Emergency Response System

A sophisticated AI-powered companion application designed specifically for elderly care, combining voice recognition, natural language processing, personalized conversation, music playback, and emergency response capabilities.

## 🎯 Project Overview

Sathi-AI is an intelligent desktop/embedded application that provides:
- **Voice Recognition & Audio Processing** using Whisper.cpp for accurate speech-to-text
- **Intelligent Conversations** powered by LLM models (Qwen 1.5-1.8B or Gemma)
- **Elderly-Centric Features** with simplified UI and accessibility features
- **Music Playback** with curated devotional songs
- **Reminder & Task Management** for medication and daily activities
- **Emergency Response System** with email alerts and emergency contact management
- **Offline-First Architecture** for privacy and reliability

## 📋 System Requirements

- **Python 3.8+**
- **Windows 10+** or **Linux/Raspberry Pi**
- **4GB RAM minimum** (8GB recommended)
- **2GB disk space** for models
- **Microphone** for voice input
- **Internet connection** (for initial setup only, optional for offline mode)

## 🚀 Quick Start Guide

### 1. Clone the Repository
```bash
git clone https://github.com/nandurkarajay/Saathi-ai.git
cd Saathi-ai
```

### 2. Create Virtual Environment
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux/Raspberry Pi
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Download Whisper.cpp Model

**[⬇️ Download Model from Drive](#)** *(Link to be provided)*

Extract the model file and place it in the `models/` directory:
```
Sathi-Ai/
└── models/
    └── Qwen1.5-1.8B.Q4_K_S.gguf  (required for LLM)
```

### 5. Configure Environment
Copy `.env.example` to `.env` and update with your settings:
```bash
cp .env.example .env
```

Edit `.env` with:
- Emergency contact email
- API keys (if using cloud services)
- Model preferences
- Voice recognition settings

### 6. Run the Application
```bash
python core/main.py
```

## 📦 Project Structure

```
Sathi-Ai/
├── core/                          # Main application code
│   ├── main.py                   # Application entry point
│   ├── voice_input.py            # Voice recognition (Whisper.cpp integration)
│   ├── llm_local.py              # Local LLM inference
│   ├── tts_output.py             # Text-to-speech output
│   ├── elderly_personality.py    # Personality & conversation engine
│   ├── empathy_engine.py         # Empathy & emotional intelligence
│   ├── reminder_system.py        # Reminders & notifications
│   ├── task_system.py            # Task management
│   ├── emergency_handler.py      # Emergency response system
│   ├── music_player.py           # Music playback
│   ├── wake_detection.py         # Wake word detection
│   ├── config.py                 # Configuration management
│   ├── utils.py                  # Utility functions
│   └── ui_styles.py              # UI styling
├── data/                         # Runtime data & logs
│   ├── api_quota.json
│   ├── connectivity_status.json
│   └── emergency_log.json
├── models/                       # ML Models
│   └── Qwen1.5-1.8B.Q4_K_S.gguf # LLM Model
├── songs/                        # Devotional music collection
├── whisper.cpp/                  # Voice recognition engine
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment variables template
└── README.md                     # This file
```

## 🎤 Voice Recognition (Whisper.cpp)

This project uses **Whisper.cpp** for accurate, offline voice-to-text conversion:

- **Model**: OpenAI Whisper (quantized for efficiency)
- **Language Support**: Multi-language (including Hindi)
- **Offline Processing**: No internet required
- **GPU Support**: Optional CUDA/OpenGL acceleration

### Installing Whisper.cpp

**For Windows (Pre-built):**
```bash
cd whisper.cpp
# The pre-compiled binary is already included
```

**For Linux/Raspberry Pi:**
```bash
cd whisper.cpp
mkdir build && cd build
cmake ..
make
cd ..
```

**For macOS:**
```bash
cd whisper.cpp
mkdir build && cd build
cmake ..
make
```

## 🧠 AI Models

### LLM Configuration
The application supports two LLM backends:

**1. Local Quantized Model (Default)**
- Model: Qwen1.5-1.8B quantized
- Size: ~1.2GB
- Inference Speed: ~2-5 tokens/second
- No API keys required

**2. Gemma Model (Alternative)**
- Lightweight alternative
- Configure in `core/config.py`

## 🔧 Configuration

Edit `core/config.py` to customize:
```python
# Voice recognition
WHISPER_MODEL = "base.en"
LANGUAGE = "hindi"

# LLM settings
LLM_MODEL_PATH = "models/Qwen1.5-1.8B.Q4_K_S.gguf"
MAX_TOKENS = 256

# UI settings
FONT_SIZE = 14  # For accessibility
```

## 🚨 Emergency Features

### Setting Up Emergency Contacts
1. Edit `core/config.py` with emergency email
2. Configure SMTP settings in `.env`
3. Test with emergency trigger command

### Emergency Response Flow
- User can trigger emergency with voice command or button
- System sends email alerts to configured contacts
- Emergency log is maintained in `data/emergency_log.json`

## 📱 Features

### ✅ Core Features
- [x] Voice input with Whisper.cpp
- [x] Natural conversation with LLM
- [x] Text-to-speech output
- [x] Reminder system
- [x] Task management
- [x] Emergency alerts
- [x] Music player (Devotional)
- [x] Wake word detection
- [x] Offline mode support
- [x] Elderly-friendly UI

### 🎯 Planned Features
- [ ] Mobile app (Android/iOS)
- [ ] Cloud sync option
- [ ] Multi-language UI
- [ ] Advanced emotion detection
- [ ] Integration with wearables

## 🔐 Security & Privacy

- **Offline-First**: No data sent to cloud by default
- **Encrypted Storage**: Sensitive data encrypted locally
- **No Tracking**: No telemetry or user tracking
- **Open Source**: Fully auditable code

See [SECURITY_SETUP.md](SECURITY_SETUP.md) for detailed security instructions.

## 🐛 Troubleshooting

### Voice Recognition Not Working
```bash
# Check Whisper.cpp installation
cd whisper.cpp && ./main -h

# Verify model path in config.py
# Test with: python -c "from core.voice_input import VoiceInput; vi = VoiceInput(); print('OK')"
```

### Model Loading Issues
```bash
# Verify model exists
ls -la models/

# Check file integrity
# Reinstall from provided link
```

### Low Performance
- Reduce `MAX_TOKENS` in config
- Use GPU acceleration if available
- Close other applications

## 📚 Documentation

- [PRD - Product Requirements](Sathi-AI_PRD.md)
- [Security Setup Guide](SECURITY_SETUP.md)
- [Setup Guide for Raspberry Pi](pi_setup_guide.md)

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

This project is provided as-is for elderly care use. Please review licensing terms before commercial deployment.

## 👥 Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Check existing documentation
- Review the troubleshooting guide

## 🙏 Acknowledgments

- **Whisper.cpp** - For accurate voice recognition
- **Qwen Team** - For efficient LLM models
- **Community** - For feedback and contributions

---

**Last Updated**: May 2026
**Status**: Active Development
**Maintainer**: @nandurkarajay

