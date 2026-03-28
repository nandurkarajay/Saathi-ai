"""
Configuration settings for Sathi-AI Elderly Care Companion
"""

import os
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / 'data'
LOGS_DIR = DATA_DIR / 'logs'
DB_PATH = DATA_DIR / 'sathi.db'
CHAT_CONTEXT_PATH = DATA_DIR / 'chat_context.txt'

# Audio settings
AUDIO_SAMPLE_RATE = 16000
AUDIO_CHANNELS = 1
SILENCE_THRESHOLD = 800
SILENCE_DURATION = 1.5
MAX_RECORDING_DURATION = 30

# TTS settings
TTS_RATE = 120  # Slower for elderly users
TTS_VOLUME = 0.9
TTS_USE_MALE_VOICE = False

# Wake word settings
WAKE_WORDS = [
    "hey sathi", "hi sathi", "ok sathi",
    "hello sathi", "dear sathi", "sathi please",
    "sathi help", "listen sathi", "sathi are you there",
]

# LLM settings
LLM_MODEL_PATH = PROJECT_ROOT / 'models' / 'ggml-small-q8_0.bin'

# Logging settings
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"

# Scheduler settings
SCHEDULER_CHECK_INTERVAL = 60  # seconds

# Reminder settings
DEFAULT_REMINDER_RING_ENABLED = True
DEFAULT_REMINDER_REPEAT_DAILY = True

# Local LLM settings (Qwen model for offline fallback)
LOCAL_LLM_MODEL_PATH = PROJECT_ROOT / 'models' / 'Qwen1.5-1.8B.Q4_K_S.gguf'
LOCAL_LLM_ENABLED = True
LOCAL_LLM_MAX_TOKENS = 150  # Match Gemini for consistent short responses
LOCAL_LLM_TEMPERATURE = 0.5  # Balanced for creativity
LOCAL_LLM_CONTEXT_LENGTH = 2048
LOCAL_LLM_N_THREADS = 4
LOCAL_LLM_BATCH_SIZE = 512

# News API settings
NEWS_API_KEY = os.getenv('NEWS_API_KEY', None)  # Get from environment variable
GNEWS_API_KEY = os.getenv('GNEWS_API_KEY', None)  # Get from environment variable
NEWS_LOCATION = 'Maharashtra'
NEWS_COUNTRY = 'in'
NEWS_CATEGORY = 'general'
NEWS_MAX_HEADLINES = 5
NEWS_TIMEOUT = 10  # seconds

# Music player settings
MUSIC_SONGS_DIR = PROJECT_ROOT / 'songs'
MUSIC_CACHE_DURATION = 30  # seconds
MUSIC_SIMILARITY_THRESHOLD = 0.6  # 60% for fuzzy matching
MUSIC_SUPPORTED_FORMATS = ['mp3', 'wav', 'm4a', 'flac', 'ogg']
MUSIC_PLAYERS = ['mpg123', 'ffplay', 'vlc', 'mplayer']  # Preferred order
