# Real-Time Transcription with Wake Word Detection

This project implements a local, real-time audio transcription system with wake word detection using Python. It captures audio from a microphone, detects a specified wake word (e.g., "Hey Agent"), and transcribes speech using `faster-whisper`, sending results to a local LLM via Ollama.

## Features
- **Real-Time Transcription**: Processes audio in 1-second chunks using `faster-whisper` for low-latency transcription.
- **Wake Word Detection**: Uses `pvporcupine` to trigger transcription only when a wake word is detected.
- **Local Processing**: Runs entirely offline with CPU or GPU support.
- **Configurable**: Adjustable chunk size, model size, and overlap for performance tuning.

## Requirements
- Python 3.8+
- Libraries: `faster-whisper`, `pyaudio`, `pvporcupine`, `numpy`
- Picovoice access key (free from Picovoice website)
- A decent microphone for clear audio input

## Installation
1. Install dependencies:
   ```bash
   pip install faster-whisper pyaudio pvporcupine numpy
   ```
2. Obtain a Picovoice access key and wake word model (e.g., "Hey Agent") from [Picovoice Console](https://console.picovoice.ai).
3. Ensure a microphone is connected and configured.


## Additional Installation Instructions

Mac
```
brew install portaudio
brew install ffmpeg
brew install sox (for tne nodejs version)
```

venv
```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage - Basic transcription

Run the script:
```bash
python transcribe.py
```
Say the wake word (e.g., "Hey Robo") followed by your command. Transcriptions are printed and can be piped to an Ollama LLM.

## Usage - Transcription Service with Browser Client

Run the service:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

OR on Apple Silicon

Run the service:
```bash
uvicorn main_coreml:app --reload --host 0.0.0.0 --port 8000
```

This will start the server:
```bash
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```


## Code Overview
```python
from faster_whisper import WhisperModel
import pyaudio
import numpy as np
import pvporcupine
import queue
import threading

# Configuration
MODEL_SIZE = "tiny"  # Options: tiny, base, small (tiny/base for real-time)
SAMPLE_RATE = 16000
CHUNK_SIZE = 512  # Frames per buffer (adjust for latency vs. CPU load)
AUDIO_FORMAT = pyaudio.paInt16
CHANNELS = 1
OVERLAP_SECONDS = 0.5  # Overlap for transcription context

# Initialize models
model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")  # Use "cuda" for GPU
porcupine = pvporcupine.create(access_key="YOUR_PICOVOICE_ACCESS_KEY", keywords=["hey agent"])

# Audio queue and wake word flag
audio_queue = queue.Queue()
wake_detected = threading.Event()

def audio_callback(in_data, frame_count, time_info, status):
    audio_data = np.frombuffer(in_data, dtype=np.int16)
    audio_queue.put(audio_data)
    return (in_data, pyaudio.paContinue)

def wake_word_detection():
    while True:
        audio_data = audio_queue.get()
        keyword_index = porcupine.process(audio_data)
        if keyword_index >= 0:
            print("Wake word detected!")
            wake_detected.set()

def transcribe_stream():
    buffer = np.array([], dtype=np.float32)
    while True:
        if wake_detected.is_set():
            audio_data = audio_queue.get()
            audio_float = audio_data.astype(np.float32) / 32768.0
            buffer = np.append(buffer, audio_float)
            if len(buffer) >= SAMPLE_RATE:
                segments, _ = model.transcribe(buffer, language="en", vad_filter=True)
                for segment in segments:
                    print(f"Transcription: {segment.text}")
                    # Pipe segment.text to Ollama LLM here
                buffer = buffer[int(SAMPLE_RATE * OVERLAP_SECONDS):]  # Slide window
            wake_detected.clear()

# Set up PyAudio stream
p = pyaudio.PyAudio()
stream = p.open(format=AUDIO_FORMAT, channels=CHANNELS, rate=SAMPLE_RATE,
                input=True, frames_per_buffer=CHUNK_SIZE, stream_callback=audio_callback)

# Start threads
wake_thread = threading.Thread(target=wake_word_detection, daemon=True)
transcription_thread = threading.Thread(target=transcribe_stream, daemon=True)
wake_thread.start()
transcription_thread.start()

# Start stream
print("Listening for wake word...")
stream.start_stream()
try:
    while True:
        pass
except KeyboardInterrupt:
    print("Stopping...")
    stream.stop_stream()
    stream.close()
    p.terminate()
    porcupine.delete()
```

## Configuration Tips
- **Model Size**: Use `tiny` or `base` for real-time performance; `small` for better accuracy if hardware allows.
- **Chunk Size**: Decrease `CHUNK_SIZE` (e.g., 256) for lower latency or increase (e.g., 1024) for less CPU load.
- **Overlap**: Adjust `OVERLAP_SECONDS` to balance context and performance.
- **GPU Support**: Set `device="cuda"` in `WhisperModel` for faster transcription if a compatible GPU is available.
- **Microphone**: Use a high-quality microphone to minimize noise and improve accuracy.

## Integration with Ollama
- Pipe transcriptions (`segment.text`) to your local Ollama LLM by adding a function call in the `transcribe_stream` loop.
- Example: Send `segment.text` via a REST API or socket to your LLM endpoint.

## Troubleshooting
- **Choppy Audio**: Reduce `CHUNK_SIZE` or check microphone quality.
- **Slow Transcription**: Switch to a smaller model or enable GPU support.
- **Wake Word Issues**: Ensure the correct wake word model and valid Picovoice key.

## Future Enhancements
- Save transcriptions to a file.
- Add keyword-based triggers for specific actions.
- Optimize buffer size for lower latency.

## License
MIT License - feel free to use and modify for your needs!