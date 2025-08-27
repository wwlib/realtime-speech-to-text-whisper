# Real-Time Speech-to-Text with Optional TTS

This project provides a modular, real-time speech transcription system with optional text-to-speech capabilities. It supports both standard machines and Apple Silicon with CoreML optimization, offering flexible deployment options for different use cases.

## Features

### Core Speech-to-Text
- **Real-Time Transcription**: Live audio processing with WebSocket communication
- **Platform Optimization**: Automatic Apple Silicon detection with CoreML acceleration
- **Flexible Backends**: Choose between faster-whisper and CoreML transcription
- **Web Interface**: Browser-based client with real-time transcription display

### Optional Text-to-Speech (TTS)
- **Natural Voice Synthesis**: High-quality TTS using Piper voices
- **Multiple Voice Options**: Choose from various English voice models
- **Auto-TTS Mode**: Automatic speech synthesis of transcribed text
- **Manual TTS**: On-demand text-to-speech conversion

### Architecture
- **Modular Design**: Separate STT and TTS modules for clean organization
- **Service Factory Pattern**: Automatic platform-aware service selection
- **FastAPI Backend**: Modern async web framework with WebSocket support
- **Local Processing**: Runs entirely offline for privacy and performance

## Requirements

- **Python 3.8+**
- **System Dependencies**: 
  - macOS: `brew install portaudio ffmpeg`
  - Linux: `sudo apt-get install portaudio19-dev ffmpeg`
- **Python Packages**: See `requirements.txt` and `requirements_tts.txt`
- **For TTS**: Additional Piper TTS models (auto-downloaded)

## Quick Start

### 1. Set Up Environment
```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install system dependencies (macOS)
brew install portaudio ffmpeg

# Install Python dependencies
pip install -r requirements.txt
```

### 2. STT-Only Mode (Recommended for most users)
```bash
# Start STT-only server
python main.py

# Access web interface
open http://localhost:8000
```

### 3. STT + TTS Mode (Optional)
```bash
# Install TTS dependencies
pip install -r requirements_tts.txt

# Download TTS models (interactive)
python tts/download_models.py

# Start combined STT+TTS server
python main_tts.py

# Access TTS-enabled interface
open http://localhost:8000
```


## Platform Support

### Automatic Platform Detection
The system automatically detects your platform and chooses the optimal transcription backend:

- **Apple Silicon**: Uses CoreML-optimized transcription for better performance
- **Other Platforms**: Uses faster-whisper for reliable transcription

### Manual Backend Selection
Override automatic detection with environment variables:
```bash
# Force CoreML backend (Apple Silicon only)
STT_SERVICE=coreml python main.py

# Force faster-whisper backend
STT_SERVICE=whisper python main.py
```

## Project Structure

```
├── main.py                 # STT-only server
├── main_tts.py            # STT+TTS server
├── requirements.txt       # Core dependencies
├── requirements_tts.txt   # TTS dependencies
├── stt/                   # Speech-to-text module
│   ├── base_service.py       # Base transcription interface
│   ├── service_factory.py   # Platform-aware service creation
│   ├── transcription_service.py  # faster-whisper implementation
│   ├── coreml_transcription_service.py  # CoreML implementation
│   ├── platform_detector.py # Apple Silicon detection
│   └── connection_manager.py # WebSocket connection handling
├── tts/                   # Text-to-speech module (optional)
│   ├── tts_service.py        # Piper TTS implementation
│   ├── download_models.py   # TTS model downloader
│   └── models/              # Voice model files
└── static/
    ├── index.html           # STT web interface
    └── index_tts.html       # STT+TTS web interface
```

## Configuration

### Environment Variables
- `STT_SERVICE`: Override backend selection (`whisper` or `coreml`)
- `TTS_VOICE`: Choose TTS voice model (e.g., `en_US-lessac-medium`)

### Performance Tuning
- **Model Size**: Configurable in service files (tiny, base, small, medium)
- **Audio Settings**: Adjustable chunk size and sample rate
- **GPU Support**: Automatic GPU detection for faster-whisper

## Web Interface Features

### STT-Only Interface (`index.html`)
- Real-time transcription display
- Microphone status indicator
- Connection status monitoring

### STT+TTS Interface (`index_tts.html`)
- All STT features plus:
- Auto-TTS toggle (speak transcribed text)
- Manual TTS input field
- Voice synthesis controls

## Troubleshooting

### Audio Issues
- **Microphone not detected**: Check system permissions and audio device selection
- **Poor transcription quality**: Verify microphone quality and background noise levels
- **Audio dropouts**: Adjust chunk size or check system performance

### Platform Issues
- **CoreML not available**: Ensure you're on Apple Silicon; falls back to faster-whisper automatically
- **Model loading errors**: Check available memory and disk space for model files
- **Performance issues**: Try smaller model sizes or check CPU/GPU utilization

### TTS Issues
- **No voice output**: Ensure TTS models are downloaded with `python tts/download_models.py`
- **Audio playback issues**: Check browser audio permissions and system audio settings
- **Voice quality problems**: Try different voice models or check audio codec support

### Connection Issues
- **WebSocket connection failed**: Check firewall settings and port availability
- **Browser compatibility**: Use modern browsers with WebSocket and Web Audio API support
- **CORS issues**: Ensure proper localhost/origin configuration

## Advanced Usage

### Custom Deployment
- Modify host/port settings in `main.py` or `main_tts.py`
- Configure reverse proxy for production deployment
- Set up SSL/TLS for secure connections

### Integration Examples
- **REST API**: Send audio data via HTTP POST to `/transcribe` endpoint
- **WebSocket**: Real-time bidirectional communication for live applications
- **Batch Processing**: Process audio files through the transcription services

### Development
- **Service Extension**: Inherit from `BaseTranscriptionService` for custom backends
- **TTS Customization**: Modify `TTSService` for different voice synthesis engines
- **UI Customization**: Edit HTML/CSS/JS files in `static/` directory

## Related Documentation

- [`README_TTS.md`](README_TTS.md) - Detailed TTS setup and configuration
- [`TTS_IMPLEMENTATION.md`](TTS_IMPLEMENTATION.md) - Technical TTS implementation details
- [`MODULAR_ARCHITECTURE.md`](MODULAR_ARCHITECTURE.md) - Architecture and design decisions

## License

MIT License - feel free to use and modify for your needs!