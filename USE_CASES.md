# Project Use Cases

This project supports two distinct use cases with different architectural approaches:

## Use Case 1: Audio Transcription Service 🎙️
**Purpose**: Professional audio transcription for live events/meetings
**Setup**: Mac Mini receives audio from sound board via USB audio interface
**Output**: Broadcasts text transcriptions to web clients in real-time

### Architecture:
- **Audio Input**: USB audio interface → Mac Mini
- **Processing**: STT (Speech-to-Text) transcription 
- **Distribution**: WebSocket server → Multiple web clients
- **Use Cases**: Live events, meetings, accessibility services

### Key Components:
- `main.py` - WebSocket server for transcription broadcasting
- USB audio interface support
- Multi-client WebSocket distribution
- Real-time transcription streaming

---

## Use Case 2: Interactive AI Agent 🤖
**Purpose**: Voice-enabled AI chat agent with browser interface
**Setup**: Browser-based STT input and TTS output for multiple clients
**Interaction**: Full conversational AI with speech input/output

### Architecture:
- **Audio Input**: Browser microphone → WebSocket → STT
- **Processing**: AI agent logic + response generation
- **Audio Output**: TTS → WebSocket → Browser audio playback
- **Multi-client**: Each client has independent conversation

### Key Components:
- `speech_agent_integration.py` - Direct Python integration
- `main_tts.py` - WebSocket server with TTS support
- Browser-based audio capture/playback
- AI agent integration framework

---

## Architectural Benefits

### Use Case 1 (Transcription Service):
- **Dedicated hardware**: Professional USB audio interface
- **One-to-many**: Single audio source → multiple text recipients
- **Broadcast model**: Real-time transcription distribution

### Use Case 2 (AI Agent):
- **Browser isolation**: Natural audio separation (STT/TTS)
- **Many-to-many**: Multiple clients → individual conversations
- **Interactive model**: Full duplex voice conversations

---

## Integration Notes

Both use cases leverage the same core STT/TTS technology but with different:
- **Audio sources**: USB interface vs browser microphone
- **Distribution patterns**: Broadcast vs individual sessions
- **Interaction models**: One-way transcription vs two-way conversation

The modular architecture supports both use cases through the same underlying services with different WebSocket communication patterns.
