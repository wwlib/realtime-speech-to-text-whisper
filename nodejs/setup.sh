#!/bin/bash

# Node.js Transcription Service Setup Script

echo "🎤 Setting up Node.js Real-Time Transcription Service..."
echo ""

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 16+ first:"
    echo "   Visit: https://nodejs.org/"
    exit 1
fi

# Check Node.js version
NODE_VERSION=$(node -v | cut -d'v' -f2)
REQUIRED_VERSION="16.0.0"

# if ! node -e "process.exit(require('semver').gte('$NODE_VERSION', '$REQUIRED_VERSION') ? 0 : 1)" 2>/dev/null; then
#     echo "❌ Node.js version $NODE_VERSION detected. Please upgrade to Node.js 16+ first."
#     exit 1
# fi

echo "✅ Node.js version: $(node -v)"
echo ""

# Install system dependencies on macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "🍺 Installing system dependencies with Homebrew..."
    
    if ! command -v brew &> /dev/null; then
        echo "❌ Homebrew not found. Please install Homebrew first:"
        echo "   /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
        exit 1
    fi
    
    echo "   Installing PortAudio..."
    brew install portaudio
    
    echo "   Installing FFmpeg..."
    brew install ffmpeg

    echo "   Installing SoX..."
    brew install sox
    
    echo "✅ System dependencies installed"
    echo ""
fi

# Install Node.js dependencies
echo "📦 Installing Node.js dependencies..."
npm install

if [ $? -ne 0 ]; then
    echo "❌ Failed to install Node.js dependencies"
    exit 1
fi

echo "✅ Node.js dependencies installed"
echo ""

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p temp
mkdir -p models

echo "✅ Directories created"
echo ""

# Download Whisper models (this will happen automatically on first run)
echo "🤖 Whisper models will be downloaded automatically on first run"
echo ""

echo "🎉 Setup complete!"
echo ""
echo "To start the transcription service:"
echo "   npm start"
echo ""
echo "For development with auto-reload:"
echo "   npm run dev"
echo ""
echo "The service will be available at: http://localhost:3000"
echo ""
