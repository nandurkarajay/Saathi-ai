#!/bin/bash
# Raspberry Pi 4GB Whisper Model Setup

echo "🏆 Setting up best model for Pi 4GB..."
echo "Recommended: ggml-base.bin"

# Create models directory
mkdir -p models

# Download the best model for Pi 4GB
echo "📥 Downloading ggml-base.bin (74MB)..."
wget -O models/ggml-base.bin https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin

# Verify download
if [ -f models/ggml-base.bin ]; then
    echo "✅ Model downloaded successfully!"
    echo "📊 Size: $(ls -lh models/ggml-base.bin | awk '{print $5}')"
    echo "🎯 Ready for real-time transcription on Pi 4GB!"
else
    echo "❌ Download failed!"
    exit 1
fi

# Alternative models (uncomment if needed)
# echo "📥 Alternative: Downloading ggml-tiny.bin (fastest)..."
# wget -O models/ggml-tiny.bin https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-tiny.bin

# echo "📥 Alternative: Downloading ggml-small.bin (most accurate)..."
# wget -O models/ggml-small.bin https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.bin

echo ""
echo "🔧 Update your voice_input.py:"
echo "   model_path = \"models/ggml-base.bin\""
echo ""
echo "🚀 Your Pi 4GB is ready for Sathi AI!"
