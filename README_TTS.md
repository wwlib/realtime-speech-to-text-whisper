# Realtime Speech-to-Text with Text-to-Speech

This is an enhanced version of the realtime speech-to-text application that includes **Text-to-Speech (TTS)** functionality using Piper TTS.

## Features

- **Real-time Speech Recognition**: Uses Faster Whisper for accurate, low-latency transcription
- **Text-to-Speech**: High-quality speech synthesis using Piper TTS
- **Streaming Audio**: Audio is streamed to the browser in real-time chunks
- **WebSocket Communication**: Real-time bidirectional communication between browser and server
- **Voice Activity Detection**: Automatically starts/stops recording based on speech detection

## Requirements

- Python 3.8+
- macOS (tested on M4 Mac Mini)
- USB audio interface or built-in microphone
- Modern web browser with WebSocket and Web Audio API support

## Quick Start

### 1. Install Dependencies

```bash

python -m venv .venv
source .venv/bin/activate

# Run the setup script
./setup_tts.sh

# Or install manually:
pip install -r requirements.txt
pip install -r requirements_tts.txt
```

### 2. Download TTS Models

```bash
python3 download_models.py
```

This will show you available voice models. Choose one or download all:
- `en_US-lessac-medium` - High-quality US English voice (recommended)
- `en_US-amy-medium` - Clear US English voice  
- `en_US-ryan-high` - High-quality male US English voice

### 3. Start the Server

```bash
python3 main_tts.py
```

### 4. Open the Web Interface

Navigate to `http://localhost:8000` in your browser.

## Usage

### Speech-to-Text
- The application automatically listens for speech
- When you speak, it will transcribe your words in real-time
- Transcriptions appear in the "Live Transcription" box

### Text-to-Speech
- Type text in the input field
- Click "Speak" or press Enter to synthesize speech
- Audio streams to your browser and plays immediately
- Use "Clear" to empty the input field

## Configuration

### Audio Input Device

If you need to use a specific audio input device (like a USB audio interface), update the `input_device_index` in `transcription_service.py`:

```python
stream = p.open(
    # ... other parameters ...
    input_device_index=4  # Change this to your device index
)
```

To see available devices, run any of the transcription scripts - they'll list all audio devices on startup.

### TTS Voice Model

To change the TTS voice, update the model paths in `tts_service.py`:

```python
self.model_path = os.path.join(self.models_dir, "en_US-amy-medium.onnx")
self.config_path = os.path.join(self.models_dir, "en_US-amy-medium.onnx.json")
```

### Voice Activity Detection

Adjust VAD sensitivity in `transcription_service.py`:

```python
SILENCE_THRESHOLD = 300  # Lower = more sensitive
SILENCE_DURATION_S = 0.125  # How long to wait for silence
MIN_RECORDING_DURATION_S = 1.0  # Minimum recording length
```

## File Structure

```
├── main_tts.py              # Main server with TTS support
├── transcription_service.py  # Speech-to-text service
├── tts_service.py           # Text-to-speech service
├── download_models.py       # Script to download TTS models
├── setup_tts.sh            # Setup script
├── requirements_tts.txt     # TTS-specific dependencies
├── static/
│   └── index_tts.html      # Web interface with TTS support
└── models/                 # TTS voice models (created after download)
```

## Technical Details

### Audio Processing
- **Sample Rate**: 16kHz
- **Channels**: Mono
- **Format**: 16-bit PCM
- **Chunk Size**: 1 second (16,000 samples)

### Streaming
- Audio is streamed in ~0.2 second chunks (3,200 samples)
- Uses hex encoding for binary data over WebSocket
- Browser reconstructs and plays audio using Web Audio API

### Models
- **Whisper**: `base.en` model for optimal speed/accuracy balance
- **Piper TTS**: ONNX models for fast, high-quality synthesis
- Models run efficiently on M4 Mac Mini CPU

## Troubleshooting

### Audio Issues
- Check microphone permissions in System Preferences
- Verify correct audio device index
- Test microphone with other applications

### TTS Issues
- Ensure models are downloaded: `python3 download_models.py`
- Check models directory exists and contains `.onnx` and `.onnx.json` files
- Verify Piper TTS installation: `pip install piper-tts`

### Connection Issues
- Check firewall settings
- Ensure port 8000 is available
- Try refreshing the browser page

### Performance
- M4 Mac Mini handles real-time processing well
- For slower systems, consider using smaller Whisper models
- Adjust chunk sizes if experiencing latency

## Development

To modify or extend the application:

1. **Add new TTS voices**: Download additional models and update `tts_service.py`
2. **Customize audio processing**: Modify VAD parameters in `transcription_service.py`
3. **Enhance UI**: Edit `static/index_tts.html` for interface changes
4. **Add features**: Extend WebSocket message handling in `main_tts.py`

## License

MIT License - see original project for details.
