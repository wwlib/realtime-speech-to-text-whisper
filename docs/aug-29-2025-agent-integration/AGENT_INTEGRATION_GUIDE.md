# Speech Integration Guide for Chat Agents

This guide explains how to integrate your STT and TTS modules into Python chat-based agents.

## Integration Options

### 1. **Direct Module Integration (Recommended)**

Use the `speech_agent_integration.py` module to add speech capabilities to any Python chat agent:

```python
from speech_agent_integration import SpeechEnabledAgent

class MyChatAgent:
    def __init__(self):
        self.speech_agent = SpeechEnabledAgent()
        self.speech_agent.set_transcription_handler(self.handle_user_speech)
    
    def handle_user_speech(self, transcription: str) -> str:
        # Your agent logic here
        response = self.generate_response(transcription)
        return response  # Will be spoken automatically
    
    def start(self):
        self.speech_agent.start_listening()
```

### 2. **Copy Core Modules**

Copy the following directories to your agent project:
- `stt/` - Speech-to-text services
- `tts/` - Text-to-speech services

Then import and use the services directly:

```python
from stt.service_factory import create_stt_service
from tts.tts_service import TTSService
```

### 3. **Subprocess Integration**

Run the STT/TTS server as a separate process and communicate via WebSocket:

```python
import subprocess
import websocket

# Start STT+TTS server
server_process = subprocess.Popen(["python", "main_tts.py"])

# Connect to WebSocket
ws = websocket.WebSocket()
ws.connect("ws://localhost:8000/ws")
```

## Required Dependencies

Add these to your agent's requirements:

```txt
# Core STT dependencies
faster-whisper
pyaudio
numpy
torch

# TTS dependencies  
piper-tts

# Platform-specific (Apple Silicon)
coremltools  # Only needed for CoreML backend

# Web framework (if using subprocess approach)
fastapi
uvicorn
websockets
```

## Configuration

### Environment Variables

Set these in your agent's environment:

```bash
# Force specific STT backend
export STT_SERVICE=coreml      # For Apple Silicon
export STT_SERVICE=whisper     # For other platforms

# TTS voice selection
export TTS_VOICE=en_US-amy-medium
```

### Audio Device Selection

The STT service auto-detects audio devices. To use a specific microphone:

```python
# In transcription_service.py, modify the stream opening:
stream = p.open(
    # ... other parameters ...
    input_device_index=YOUR_DEVICE_INDEX
)
```

## Integration Patterns

### Pattern 1: Callback-Based (Simple)

```python
def my_chat_handler(user_speech: str) -> str:
    # Process with your agent (OpenAI, Ollama, etc.)
    response = my_agent.process(user_speech)
    return response

speech_agent = SpeechEnabledAgent()
speech_agent.set_transcription_handler(my_chat_handler)
speech_agent.start_listening()
```

### Pattern 2: Queue-Based (Advanced)

```python
import queue
import threading

transcription_queue = queue.Queue()

def transcription_callback(text: str):
    transcription_queue.put(text)

speech_agent = SpeechEnabledAgent()
speech_agent.set_transcription_handler(transcription_callback)

# Process transcriptions in separate thread
def process_transcriptions():
    while True:
        text = transcription_queue.get()
        response = my_agent.process(text)
        speech_agent.speak(response)

threading.Thread(target=process_transcriptions, daemon=True).start()
speech_agent.start_listening()
```

### Pattern 3: Async Integration

```python
import asyncio

class AsyncChatAgent:
    def __init__(self):
        self.speech_agent = SpeechEnabledAgent()
        self.speech_agent.set_transcription_handler(self.sync_handler)
    
    def sync_handler(self, text: str):
        # Bridge to async
        loop = asyncio.get_event_loop()
        loop.call_soon_threadsafe(
            lambda: asyncio.create_task(self.async_handler(text))
        )
    
    async def async_handler(self, text: str):
        # Your async agent logic
        response = await self.process_async(text)
        self.speech_agent.speak(response)
```

## Popular Framework Integration

### LangChain

```python
from langchain.agents import initialize_agent
from langchain.llms import OpenAI

llm = OpenAI()
agent = initialize_agent([...], llm)

def langchain_handler(text: str) -> str:
    result = agent.run(text)
    return result

speech_agent = SpeechEnabledAgent()
speech_agent.set_transcription_handler(langchain_handler)
```

### Rasa

```python
from rasa.core.agent import Agent

rasa_agent = Agent.load("path/to/your/model")

def rasa_handler(text: str) -> str:
    response = rasa_agent.handle_text(text)
    return response[0]['text'] if response else "I didn't understand"

speech_agent = SpeechEnabledAgent()
speech_agent.set_transcription_handler(rasa_handler)
```

### Botframework

```python
from botbuilder.core import TurnContext

def botframework_handler(text: str) -> str:
    # Create mock context and process
    context = create_mock_context(text)
    response = my_bot.on_message_activity(context)
    return response

speech_agent = SpeechEnabledAgent()
speech_agent.set_transcription_handler(botframework_handler)
```

## Performance Optimization

### 1. Model Selection

Choose STT models based on your needs:
- `tiny.en` - Fastest, least accurate
- `base.en` - Good balance (recommended)
- `small.en` - Better accuracy
- `medium.en` - Best accuracy, slower

### 2. Audio Settings

Adjust for your environment:
```python
# In transcription_service.py
SILENCE_THRESHOLD = 300  # Increase for noisy environments
SILENCE_DURATION_S = 0.125  # Reduce for faster response
MIN_RECORDING_DURATION_S = 1.0  # Reduce for shorter phrases
```

### 3. TTS Optimization

Use different voice models:
- `en_US-amy-low` - Fastest
- `en_US-amy-medium` - Good quality
- `en_US-amy-high` - Best quality

## Troubleshooting

### Common Issues

1. **Microphone not detected**
   - Check audio permissions
   - Verify device index in `transcription_service.py`

2. **TTS models not found**
   ```bash
   python tts/download_models.py
   ```

3. **Import errors**
   - Ensure all dependencies are installed
   - Check Python path includes STT/TTS modules

4. **Audio feedback loops**
   - The system has built-in feedback prevention
   - Adjust `similarity_threshold` if needed

5. **Performance issues**
   - Use smaller models for faster response
   - Check CPU/memory usage
   - Consider running STT/TTS in separate processes

### Debug Mode

Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Security Considerations

### Local Processing
- All speech processing happens locally
- No data sent to external services (unless you integrate external LLMs)

### Audio Privacy
- Audio is processed in real-time
- No audio files are saved by default
- Transcriptions are kept in memory only

### Network Security
- If using WebSocket integration, ensure proper authentication
- Use HTTPS/WSS for production deployments

## Deployment Options

### Development
```bash
python your_agent.py  # Direct integration
```

### Production
```bash
# Using systemd service
sudo systemctl start your-speech-agent

# Using Docker
docker run -p 8000:8000 your-speech-agent

# Using process manager
pm2 start your_agent.py --interpreter python3
```

## Example Project Structure

```
your_agent_project/
├── requirements.txt
├── main.py                    # Your main agent
├── speech_integration.py      # Copy from this project
├── stt/                       # Copy entire directory
├── tts/                       # Copy entire directory
├── config/
│   ├── audio_settings.py
│   └── model_config.py
└── utils/
    ├── conversation_manager.py
    └── response_generator.py
```

This integration approach gives you full control over the speech capabilities while maintaining the modular design of your original STT/TTS system.
