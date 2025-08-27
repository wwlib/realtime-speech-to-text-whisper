#!/bin/bash

# Setup script for Realtime Speech-to-Text with TTS
# This script installs all required dependencies and downloads TTS models

echo "Setting up Realtime Speech-to-Text with TTS..."
echo "============================================="

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed."
    exit 1
fi

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    echo "Error: pip3 is required but not installed."
    exit 1
fi

echo "Installing base requirements..."
pip3 install -r requirements.txt

echo ""
echo "Installing TTS requirements..."
pip3 install -r requirements_tts.txt

echo ""
echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Download TTS models: python3 tts/download_models.py"
echo "2. Start the transcription server: python3 main_tts.py"
echo "3. Open http://localhost:8000 in your browser"
echo ""
echo "Note: Make sure your microphone is connected and configured."
