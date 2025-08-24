import asyncio
import queue
import threading
import time
import numpy as np
import pyaudio
from faster_whisper import WhisperModel

# --- Configuration ---
MODEL_SIZE = "base.en"
COMPUTE_TYPE = "int8"
DEVICE = "cpu"
SAMPLE_RATE = 16000
CHUNK_DURATION_S = 1.0
CHUNK_SAMPLES = int(SAMPLE_RATE * CHUNK_DURATION_S)
CHANNELS = 1
AUDIO_FORMAT = pyaudio.paInt16

# --- VAD Configuration ---
SILENCE_THRESHOLD = 300  # RMS energy threshold for silence
SILENCE_DURATION_S = 2.0  # How many seconds of silence before stopping recording
MIN_RECORDING_DURATION_S = 1.0  # Minimum recording duration to avoid very short clips

class TranscriptionService:
    def __init__(self, manager):
        self.manager = manager
        self.audio_queue = queue.Queue()
        self.stop_event = threading.Event()
        self.model = WhisperModel(MODEL_SIZE, device=DEVICE, compute_type=COMPUTE_TYPE)
        print("Transcription model loaded.")

    def audio_callback(self, in_data, frame_count, time_info, status):
        """Puts audio data into a queue; called by PyAudio."""
        self.audio_queue.put(np.frombuffer(in_data, dtype=np.int16))
        return (None, pyaudio.paContinue)

    def stop(self):
        """Signal the service to stop gracefully."""
        print("Stopping transcription service...")
        self.stop_event.set()

    def run(self, loop):
        """Main loop for the transcription service."""
        asyncio.set_event_loop(loop)
        p = pyaudio.PyAudio()

        try:
            stream = p.open(
                format=AUDIO_FORMAT,
                channels=CHANNELS,
                rate=SAMPLE_RATE,
                input=True,
                frames_per_buffer=CHUNK_SAMPLES,
                stream_callback=self.audio_callback,
            )
        except OSError as e:
            print(f"Error opening audio stream: {e}")
            print("Please ensure a microphone is connected and configured.")
            p.terminate()
            return

        stream.start_stream()
        print("Audio stream started. Service is running.")

        while not self.stop_event.is_set():
            try:
                # --- Phase 1: Listen for Voice Activity ---
                print("Listening for speech...")
                
                # Wait for audio activity
                speech_detected = False
                first_chunk = None
                
                while not speech_detected and not self.stop_event.is_set():
                    try:
                        audio_chunk = self.audio_queue.get(timeout=1)
                        
                        # Check for voice activity using RMS
                        rms = np.sqrt(np.mean(audio_chunk.astype(np.float32)**2))
                        
                        if rms > SILENCE_THRESHOLD:
                            # Quick transcription check to confirm it's speech
                            audio_float = audio_chunk.astype(np.float32) / 32768.0
                            segments, _ = self.model.transcribe(
                                audio_float,
                                language="en",
                                vad_filter=True,
                                vad_parameters=dict(min_silence_duration_ms=500),
                            )
                            
                            transcription = "".join(segment.text for segment in segments).strip()
                            
                            if transcription:
                                print(f"Speech detected: '{transcription}'")
                                speech_detected = True
                                first_chunk = audio_chunk
                    
                    except queue.Empty:
                        continue
                
                if self.stop_event.is_set():
                    break

                # --- Phase 2: Record Until Silence ---
                print("Recording speech...")
                
                audio_buffer = []
                if first_chunk is not None:
                    audio_buffer.append(first_chunk)
                
                silence_start_time = None
                recording_start_time = time.time()
                
                # Clear any old audio from the queue
                while not self.audio_queue.empty():
                    try:
                        self.audio_queue.get_nowait()
                    except queue.Empty:
                        break

                while not self.stop_event.is_set():
                    try:
                        audio_chunk = self.audio_queue.get(timeout=0.5)
                        audio_buffer.append(audio_chunk)

                        # RMS-based VAD
                        rms = np.sqrt(np.mean(audio_chunk.astype(np.float32)**2))

                        if rms < SILENCE_THRESHOLD:
                            if silence_start_time is None:
                                silence_start_time = time.time()
                            elif time.time() - silence_start_time > SILENCE_DURATION_S:
                                print("Silence detected, stopping recording.")
                                break
                        else:
                            # Reset silence timer if speech is detected
                            silence_start_time = None

                    except queue.Empty:
                        # If the queue is empty, check the silence timer
                        if silence_start_time and (time.time() - silence_start_time > SILENCE_DURATION_S):
                            print("Silence detected (timeout), stopping recording.")
                            break
                        continue

                # --- Phase 3: Transcribe Complete Recording ---
                recording_duration = time.time() - recording_start_time
                
                if audio_buffer and recording_duration >= MIN_RECORDING_DURATION_S:
                    # Concatenate chunks and convert to float32
                    audio_data = np.concatenate(audio_buffer, axis=0)
                    audio_float = audio_data.astype(np.float32) / 32768.0

                    print("Transcribing complete recording...")
                    segments, _ = self.model.transcribe(
                        audio_float, 
                        language="en",
                        vad_filter=True,
                        vad_parameters=dict(min_silence_duration_ms=500)
                    )
                    
                    transcription = " ".join(segment.text for segment in segments).strip()

                    if transcription:
                        print(f"Final transcription: '{transcription}'")
                        # Broadcast the transcription to all connected clients
                        asyncio.run_coroutine_threadsafe(
                            self.manager.broadcast(transcription), loop
                        )
                    else:
                        print("No speech detected in recording.")
                else:
                    print("Recording too short, skipping transcription.")

            except Exception as e:
                print(f"An error occurred in the transcription loop: {e}")
                break
        
        # Cleanup
        stream.stop_stream()
        stream.close()
        p.terminate()
        print("Transcription service stopped.")
