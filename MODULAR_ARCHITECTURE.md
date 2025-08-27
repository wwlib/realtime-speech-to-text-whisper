# Modular Architecture Guide

This document describes the new modular architecture for the realtime speech-to-text system.

## Project Structure

```
realtime-speech-to-text-whisper/
├── main.py                     # STT-only server
├── main_tts.py                 # STT + TTS combined server
├── stt/                        # Speech-to-Text module
│   ├── __init__.py
│   ├── base_service.py         # Abstract base class for STT services
│   ├── connection_manager.py   # WebSocket connection management
│   ├── platform_detector.py    # Apple Silicon detection
│   ├── service_factory.py      # STT service factory
│   ├── transcription_service.py # Faster-whisper implementation
│   └── coreml_transcription_service.py # CoreML implementation
├── tts/                        # Text-to-Speech module
│   ├── __init__.py
│   ├── tts_service.py          # Piper TTS implementation
│   └── models/                 # TTS voice models
└── static/                     # Web interface files
```

## Deployment Options

### 1. STT-Only Server (main.py)

For transcription-only applications:

```bash
# Auto-detect best STT service for platform
python main.py

# Force specific STT service
STT_SERVICE=faster-whisper python main.py
STT_SERVICE=coreml python main.py        # Apple Silicon only

# Custom port
PORT=8080 python main.py
```

### 2. STT + TTS Combined Server (main_tts.py)

For applications requiring both transcription and speech synthesis:

```bash
# Auto-detect best STT service + TTS
python main_tts.py

# Force specific STT service with TTS
STT_SERVICE=faster-whisper python main_tts.py
STT_SERVICE=coreml python main_tts.py    # Apple Silicon only

# Custom port
PORT=8080 python main_tts.py
```

## Platform Detection

The system automatically detects Apple Silicon and selects the optimal STT service:

- **Apple Silicon (M1/M2/M3)**: Recommends CoreML for hardware acceleration
- **Other platforms**: Uses faster-whisper

Override with `STT_SERVICE` environment variable.

## Service Architecture

### Base Classes

- `BaseTranscriptionService`: Abstract base for all STT implementations
- `ConnectionManager`: WebSocket connection and client settings management

### STT Services

- `TranscriptionService`: faster-whisper implementation (cross-platform)
- `CoreMLTranscriptionService`: Apple CoreML implementation (Apple Silicon only)

### TTS Service

- `TTSService`: Piper TTS implementation with queue-based processing

### Service Factory

- `create_stt_service()`: Intelligently creates appropriate STT service

## Environment Variables

- `STT_SERVICE`: Service selection (`auto`, `faster-whisper`, `coreml`)
- `PORT`: Server port (default: 8000)

## API Endpoints

### Health Check
```
GET /health
```

### Server Information
```
GET /info
```

### WebSocket
```
WS /ws
```

## Migration from Legacy Code

Legacy files have been renamed with `_old` suffix:
- `main.py` → `main_old.py`
- `main_tts.py` → `main_tts_old.py`

The new modular system provides backward compatibility while enabling flexible deployment scenarios.
