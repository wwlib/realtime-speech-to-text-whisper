# Node.js Real-Time Speech-to-Text Transcription Service

A pure JavaScript implementation of the real-time speech transcription service using Node.js and Whisper. This version provides the same functionality as the Python implementation but runs entirely in JavaScript with no cloud dependencies.

## ✅ Implementation Status

**This Node.js version is now fully implemented and ready to use!**

## 🔧 Fixing whisper-node Issues

If you encountered the `whisper-node` compilation error, the implementation has been updated to use **@xenova/transformers** which provides a more reliable WebAssembly-based Whisper implementation.

### Quick Fix:
```bash
# Remove the problematic package
npm uninstall whisper-node

# Install the updated dependencies
npm install @xenova/transformers wav

# Start the service
npm start
```

## Quick Start

1. **Prerequisites**: Ensure Node.js 16+ is installed
2. **Run setup**: `./setup.sh` (installs dependencies and system requirements)
3. **Start service**: `npm start`
4. **Open browser**: Navigate to `http://localhost:3000`
5. **Begin transcription**: Audio will be captured and transcribed automatically

## 📁 Project Structure

```
nodejs/
├── src/
│   ├── audioCapture.js         # Audio recording and VAD
│   ├── transcriptionEngine.js  # Whisper integration
│   ├── webSocketManager.js     # Real-time communication
│   └── transcriptionService.js # Main service orchestrator
├── public/
│   ├── index.html             # Web interface
│   ├── styles.css             # Responsive styling
│   └── script.js              # Client-side logic
├── server.js                  # Express server and entry point
├── config.js                  # Centralized configuration
├── package.json               # Dependencies and scripts
└── setup.sh                   # Automated setup script
```

## Overview

This Node.js implementation offers:
- **Pure JavaScript**: Single language stack for easier maintenance
- **Local Processing**: Runs entirely offline using local Whisper models
- **Real-Time WebSocket Communication**: Live transcription feed to browser clients
- **Voice Activity Detection**: Intelligent recording based on speech detection
- **Cross-Platform**: Works on macOS, Windows, and Linux
- **No External APIs**: No internet required after initial setup

## Architecture

```
┌─────────────────┐    WebSocket    ┌─────────────────┐
│   Browser       │ ◄─────────────► │   Node.js       │
│   Client        │                 │   Server        │
│                 │                 │                 │
│ - Live Display  │                 │ - Audio Capture │
│ - Auto-scroll   │                 │ - VAD Detection │
│ - Reconnection  │                 │ - Whisper Model │
└─────────────────┘                 │ - WebSocket     │
                                    └─────────────────┘
                                            │
                                            ▼
                                    ┌─────────────────┐
                                    │   Whisper.cpp   │
                                    │   (via Node.js  │
                                    │    bindings)    │
                                    └─────────────────┘
```

## Technology Stack

### Core Dependencies
- **@xenova/transformers**: Modern WebAssembly-based Whisper implementation
- **express**: Web server framework for serving static files
- **ws**: WebSocket library for real-time communication
- **node-record-lpcm16**: Cross-platform audio recording
- **wav**: WAV file format handling for audio processing

### Audio Processing
- **Web Audio API**: For browser-based audio processing (alternative approach)
- **node-portaudio**: Lower-level audio interface (alternative to node-record-lpcm16)
- **wav**: WAV file format handling for temporary audio files

## Features

### Voice Activity Detection (VAD)
- **Energy-based Detection**: RMS energy calculation to detect speech
- **Configurable Thresholds**: Adjustable silence/speech detection levels
- **Dynamic Recording**: Records only when speech is detected
- **Minimum Duration**: Prevents very short clips from being processed

### Transcription Quality
- **Model Selection**: Support for all Whisper model sizes (tiny, base, small, medium, large)
- **Language Optimization**: English-optimized models for better performance
- **Context Buffering**: Accumulates audio for better transcription accuracy
- **Error Handling**: Robust error recovery and logging

### Web Interface
- **Real-time Display**: Live transcription text appears as spoken
- **Auto-scrolling**: Automatically scrolls to show latest transcription
- **Connection Status**: Visual indicators for WebSocket connection state
- **Responsive Design**: Works on desktop and mobile browsers
- **Reconnection Logic**: Automatically reconnects if connection is lost

## Implementation Plan

### Phase 1: Core Audio Processing
```javascript
// Example structure for audio capture and processing
const recorder = require('node-record-lpcm16');
const whisper = require('whisper-node');

class AudioProcessor {
  constructor() {
    this.model = null;
    this.isRecording = false;
    this.audioBuffer = [];
  }

  async initialize() {
    // Load Whisper model
    this.model = await whisper.load('base.en');
  }

  startListening() {
    // Configure audio recording
    const recording = recorder.record({
      sampleRate: 16000,
      channels: 1,
      audioType: 'wav'
    });

    // Process audio chunks for VAD
    recording.on('data', (chunk) => {
      this.processAudioChunk(chunk);
    });
  }

  processAudioChunk(chunk) {
    // Voice Activity Detection
    const energy = this.calculateRMS(chunk);
    
    if (this.isVoiceActivity(energy)) {
      this.addToBuffer(chunk);
    } else if (this.hasRecordedAudio()) {
      this.transcribeBuffer();
    }
  }
}
```

### Phase 2: WebSocket Server
```javascript
// WebSocket server for real-time communication
const WebSocket = require('ws');
const express = require('express');

class TranscriptionServer {
  constructor() {
    this.app = express();
    this.server = null;
    this.wss = null;
    this.clients = new Set();
  }

  start(port = 3000) {
    // Serve static files
    this.app.use(express.static('public'));
    
    // Start HTTP server
    this.server = this.app.listen(port);
    
    // Create WebSocket server
    this.wss = new WebSocket.Server({ server: this.server });
    
    this.wss.on('connection', (ws) => {
      this.clients.add(ws);
      
      ws.on('close', () => {
        this.clients.delete(ws);
      });
    });
  }

  broadcast(message) {
    this.clients.forEach(client => {
      if (client.readyState === WebSocket.OPEN) {
        client.send(message);
      }
    });
  }
}
```

### Phase 3: Frontend Integration
```html
<!-- Simple HTML client -->
<!DOCTYPE html>
<html>
<head>
    <title>Live Transcription</title>
    <style>
        /* Responsive design for transcription display */
        .transcription-container { /* styling */ }
        .status-indicator { /* connection status */ }
    </style>
</head>
<body>
    <div id="status">Connecting...</div>
    <div id="transcription-display"></div>
    
    <script>
        // WebSocket connection and real-time display
        const ws = new WebSocket('ws://localhost:3000');
        // Handle incoming transcriptions
        // Auto-scroll and display logic
    </script>
</body>
</html>
```

## Configuration Options

```javascript
// config.js - Centralized configuration
module.exports = {
  // Whisper Model Settings
  whisper: {
    model: 'base.en',        // Model size: tiny, base, small, medium, large
    language: 'en',          // Language code
    task: 'transcribe'       // transcribe or translate
  },

  // Audio Settings
  audio: {
    sampleRate: 16000,       // Sample rate in Hz
    channels: 1,             // Mono audio
    chunkDuration: 1000,     // Chunk duration in ms
    silenceThreshold: 300,   // RMS threshold for silence
    silenceDuration: 2000,   // MS of silence before stopping
    minRecordingDuration: 1000 // Minimum recording length
  },

  // Server Settings
  server: {
    port: 3000,              // HTTP server port
    staticDir: 'public',     // Static files directory
    corsEnabled: true        // Enable CORS for development
  }
};
```

## Installation and Setup

### Prerequisites
```bash
# Ensure Node.js 16+ is installed
node --version

# Install system dependencies (macOS)
brew install portaudio
brew install ffmpeg
```

### Project Setup
```bash
# Create project directory
mkdir transcription-service-nodejs
cd transcription-service-nodejs

# Initialize Node.js project
npm init -y

# Install dependencies
npm install whisper-node express ws node-record-lpcm16
npm install --save-dev nodemon

# Download Whisper models (first run)
npm run download-models
```

### Development Workflow
```bash
# Start development server with auto-reload
npm run dev

# Start production server
npm start

# Run tests
npm test
```

## Performance Considerations

### Model Selection
- **tiny.en**: ~39 MB, fastest, good for real-time on lower-end hardware
- **base.en**: ~74 MB, best balance of speed and accuracy for most use cases
- **small.en**: ~244 MB, higher accuracy, requires more CPU/memory
- **medium.en**: ~769 MB, excellent accuracy, suitable for powerful machines
- **large-v2**: ~1550 MB, best accuracy, requires significant resources

### Optimization Strategies
- **Streaming Processing**: Process audio in chunks to reduce latency
- **Buffer Management**: Efficient memory usage for audio buffers
- **Connection Pooling**: Manage WebSocket connections efficiently
- **Model Caching**: Keep Whisper model loaded in memory
- **Audio Compression**: Optimize audio data transmission

## Use Cases

### Church Services
- Live transcription for hearing-impaired congregation members
- Multiple client connections for different devices
- Reliable offline operation during services
- Clear, readable text display on various screen sizes

### Meetings and Conferences
- Real-time meeting transcription
- Multi-device access for participants
- Archive transcriptions for later review
- Integration with existing web applications

### Accessibility Applications
- Live captioning for events
- Educational lecture transcription
- Broadcast accessibility compliance
- Personal transcription for hearing aid users

## Advantages Over Python Implementation

### Development Benefits
- **Single Language**: JavaScript for both frontend and backend
- **NPM Ecosystem**: Rich package ecosystem for audio and web technologies
- **Faster Iteration**: Hot reloading and rapid development cycle
- **TypeScript Support**: Optional static typing for larger projects

### Deployment Benefits
- **Lighter Runtime**: Node.js has lower memory footprint than Python
- **Container Friendly**: Smaller Docker images, faster startup
- **Cloud Native**: Better integration with serverless and edge computing
- **Scaling**: Event-driven architecture scales well for multiple clients

### Performance Benefits
- **V8 Engine**: Highly optimized JavaScript execution
- **Async I/O**: Non-blocking operations ideal for real-time applications
- **WebSocket Native**: Built-in support for real-time communication
- **Cross-Platform**: Consistent performance across operating systems

## Future Enhancements

### Advanced Features
- **Multi-language Support**: Dynamic language detection and switching
- **Speaker Diarization**: Identify different speakers in audio
- **Custom Wake Words**: Configurable activation phrases
- **Audio Effects**: Real-time audio enhancement and noise reduction

### Integration Options
- **REST API**: HTTP endpoints for programmatic access
- **Database Storage**: Save transcriptions with timestamps
- **Authentication**: User management and access control
- **External Services**: Integration with Slack, Discord, etc.

### Performance Improvements
- **GPU Acceleration**: CUDA support for faster transcription
- **Edge Computing**: Deploy closer to audio sources
- **Caching Layers**: Redis for session and model caching
- **Load Balancing**: Handle multiple concurrent transcription sessions

## Comparison with Python Version

| Feature | Python Version | Node.js Version |
|---------|----------------|-----------------|
| Language | Python | JavaScript |
| Whisper Library | openai-whisper / faster-whisper | whisper-node |
| Web Framework | FastAPI | Express |
| WebSocket | uvicorn | ws |
| Audio Capture | PyAudio | node-record-lpcm16 |
| Performance | Excellent (CoreML) | Excellent (V8 + C++) |
| Memory Usage | Higher | Lower |
| Deployment | pip/conda | npm |
| Development Speed | Fast | Faster |
| Ecosystem | Mature AI/ML | Mature Web |

## Getting Started

The Node.js implementation will maintain feature parity with the Python version while offering the benefits of a single-language stack. The development process will follow the same three-phase approach:

1. **Phase 1**: Core transcription engine with VAD
2. **Phase 2**: WebSocket server and client communication
3. **Phase 3**: Web interface and optimization

This approach ensures a smooth transition from the working Python implementation while taking advantage of Node.js's strengths in real-time web applications.
