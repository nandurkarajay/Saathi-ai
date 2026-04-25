#!/usr/bin/env python3
"""
Raspberry Pi 4GB optimized Whisper configuration
"""

# Pi 4GB RAM optimized settings
PI_WHISPER_CONFIG = {
    # Model selection based on your 4GB RAM
    "model_options": {
        "recommended": "models/ggml-base.bin",      # Best balance
        "lightweight": "models/ggml-tiny.bin",     # Fastest
        "accurate": "models/ggml-small.bin"         # Best accuracy
    },
    
    # Performance settings for Pi 4GB
    "performance": {
        "threads": 4,                    # Pi 4 has 4 cores
        "processors": 1,                  # Single processing stream
        "no_timestamps": True,            # Faster processing
        "language": "en",                 # English only
        "translate": False,               # Skip translation
    },
    
    # Memory management
    "memory": {
        "max_audio_length": 30,          # 30 second max
        "chunk_size": 10,                # 10 second chunks
        "buffer_size": 1024,             # Smaller buffer
    },
    
    # Elderly optimizations for Pi
    "elderly_optimized": {
        "silence_threshold": 180,        # Sensitive for soft voices
        "silence_duration": 1.2,         # Quick response
        "min_speech_duration": 0.4,      # Prevent false starts
        "noise_floor_multiplier": 1.6,   # Adaptive threshold
    }
}

def get_pi_model_path(performance_level="balanced"):
    """Get appropriate model path for Pi 4GB"""
    models = PI_WHISPER_CONFIG["model_options"]
    
    if performance_level == "fast":
        return models["lightweight"]
    elif performance_level == "accurate":
        return models["accurate"]
    else:
        return models["recommended"]

def get_pi_whisper_command(model_path, audio_path, is_wake_word=False):
    """Generate optimized whisper command for Pi"""
    config = PI_WHISPER_CONFIG["performance"]
    
    command = [
        "whisper.cpp/build/bin/whisper-cli",
        "-m", model_path,
        "-f", audio_path,
        "--language", config["language"],
        "-t", str(config["threads"]),
        "--no_timestamps",
    ]
    
    if is_wake_word:
        command.extend(["--prompt", "Hey Sathi, Hi Sathi"])
    
    return command

if __name__ == "__main__":
    print("Raspberry Pi 4GB Whisper Configuration")
    print("=" * 50)
    print(f"Recommended model: {PI_WHISPER_CONFIG['model_options']['recommended']}")
    print(f"RAM usage: ~150MB / 4096MB ({3.7}% used)")
    print(f"Storage: ~74MB / 128GB ({0.06}% used)")
    print(f"Expected performance: Real-time transcription")
