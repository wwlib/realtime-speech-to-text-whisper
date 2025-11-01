import asyncio
import queue
import threading
import time
import os
import numpy as np
import pyaudio
from faster_whisper import WhisperModel
from .base_service import BaseTranscriptionService

# --- Configuration ---
MODEL_SIZE = "base.en"  # Best balance of speed and accuracy for real-time transcription
COMPUTE_TYPE = "int8"
DEVICE = "cpu"  # MPS not supported by faster-whisper, but M4 CPU is very fast
SAMPLE_RATE = 16000
CHUNK_DURATION_S = 1.0
CHUNK_SAMPLES = int(SAMPLE_RATE * CHUNK_DURATION_S)
CHANNELS = 1
AUDIO_FORMAT = pyaudio.paInt16

# Audio device configuration
AUDIO_DEVICE_INDEX = os.getenv("AUDIO_DEVICE_INDEX")  # Set to device number or None for default
if AUDIO_DEVICE_INDEX is not None:
    try:
        AUDIO_DEVICE_INDEX = int(AUDIO_DEVICE_INDEX)
    except ValueError:
        print(f"Invalid AUDIO_DEVICE_INDEX: {AUDIO_DEVICE_INDEX}, using default")
        AUDIO_DEVICE_INDEX = None

# --- VAD Configuration ---
SILENCE_THRESHOLD = 200  # Reduced from 300 - more sensitive to quiet speech
SILENCE_DURATION_S = 0.125  # How many seconds of silence before stopping recording
MIN_RECORDING_DURATION_S = 0.8  # Reduced from 1.0 - allow shorter recordings

# Debug: Print available audio devices
p = pyaudio.PyAudio()
for i in range(p.get_device_count()):
    info = p.get_device_info_by_index(i)
    print(f"Device {i}: {info['name']}")
p.terminate()


class TranscriptionService(BaseTranscriptionService):
    def __init__(self, manager):
        super().__init__(manager)
        self.audio_queue = queue.Queue()
        
        # Debug: Print available devices
        try:
            import torch
            print(f"PyTorch CUDA available: {torch.cuda.is_available()}")
            print(f"PyTorch MPS available: {torch.backends.mps.is_available()}")
        except ImportError:
            print("PyTorch not available for device detection")
        
        print(f"Attempting to load Whisper model with device='{DEVICE}', compute_type='{COMPUTE_TYPE}'")
        try:
            self.model = WhisperModel(MODEL_SIZE, device=DEVICE, compute_type=COMPUTE_TYPE)
            print(f"Transcription model loaded successfully on device: {DEVICE}")
        except Exception as e:
            print(f"Failed to load model with device '{DEVICE}': {e}")
            print("Falling back to CPU...")
            self.model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")
            print("Transcription model loaded on CPU.")

    def audio_callback(self, in_data, frame_count, time_info, status):
        """Puts audio data into a queue; called by PyAudio."""
        try:
            audio_data = np.frombuffer(in_data, dtype=np.int16)
            self.audio_queue.put(audio_data)
            # Debug: Print occasionally to verify callback is working
            if hasattr(self, '_callback_count'):
                self._callback_count += 1
                if self._callback_count % 100 == 0:  # Every 100 calls (~6 seconds at 16kHz)
                    print(f"🎤 Audio callback working: {self._callback_count} calls, queue size: {self.audio_queue.qsize()}")
            else:
                self._callback_count = 1
                print(f"🎤 Audio callback started")
            return (None, pyaudio.paContinue)
        except Exception as e:
            print(f"❌ Audio callback error: {e}")
            return (None, pyaudio.paAbort)

    def stop(self):
        """Signal the service to stop gracefully."""
        print("Stopping transcription service...")
        self.stop_event.set()

    def run(self, loop):
        """Main loop for the transcription service."""
        asyncio.set_event_loop(loop)
        p = pyaudio.PyAudio()

        try:
            # Print which device we're using
            device_msg = f"default device" if AUDIO_DEVICE_INDEX is None else f"device {AUDIO_DEVICE_INDEX}"
            print(f"Opening audio stream using {device_msg}")
            
            stream = p.open(
                format=AUDIO_FORMAT,
                channels=CHANNELS,
                rate=SAMPLE_RATE,
                input=True,
                frames_per_buffer=CHUNK_SAMPLES,
                stream_callback=self.audio_callback,
                input_device_index=AUDIO_DEVICE_INDEX  # Use configured or default input device
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
                print(f"🔄 [LOOP] Starting new iteration - listening for speech...")
                
                # Wait for audio activity
                speech_detected = False
                first_chunk = None
                phase1_attempts = 0
                
                while not speech_detected and not self.stop_event.is_set():
                    phase1_attempts += 1
                    try:
                        # Check if STT should be suppressed due to TTS playback
                        if self.manager.is_stt_suppressed():
                            # Skip processing during TTS playback/cooldown
                            # Drain all queued audio to prevent processing stale audio
                            queue_size_before = self.audio_queue.qsize()
                            while not self.audio_queue.empty():
                                try:
                                    self.audio_queue.get_nowait()
                                except queue.Empty:
                                    break
                            if queue_size_before > 0:
                                print(f"🚫 [LOOP] Cleared {queue_size_before} audio chunks during TTS suppression")
                            time.sleep(0.1)  # Brief pause during suppression
                            continue
                        
                        print(f"🎧 [LOOP] Phase 1, attempt {phase1_attempts}: Waiting for audio (queue: {self.audio_queue.qsize()})")
                        audio_chunk = self.audio_queue.get(timeout=1)
                        
                        # Check for voice activity using RMS
                        rms = np.sqrt(np.mean(audio_chunk.astype(np.float32)**2))
                        print(f"📊 [LOOP] Audio RMS: {rms:.1f} (threshold: {SILENCE_THRESHOLD})")
                        
                        if rms > SILENCE_THRESHOLD:
                            print(f"🔊 [LOOP] RMS above threshold, testing with Whisper...")
                            # Quick transcription check to confirm it's speech
                            audio_float = audio_chunk.astype(np.float32) / 32768.0
                            segments, _ = self.model.transcribe(
                                audio_float,
                                language="en",
                                vad_filter=True,
                                vad_parameters=dict(min_silence_duration_ms=300),  # Reduced from 500ms
                            )
                            
                            transcription = "".join(segment.text for segment in segments).strip()
                            
                            if transcription:
                                print(f"✅ [LOOP] Speech detected: '{transcription}'")
                                speech_detected = True
                                first_chunk = audio_chunk
                            else:
                                print(f"❌ [LOOP] No speech in Whisper transcription")
                        else:
                            print(f"🔇 [LOOP] RMS too low, continuing...")
                    
                    except queue.Empty:
                        print(f"⏰ [LOOP] Queue timeout on attempt {phase1_attempts}")
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
                        vad_parameters=dict(min_silence_duration_ms=300)  # Reduced from 500ms
                    )
                    
                    transcription = " ".join(segment.text for segment in segments).strip()

                    if transcription:
                        print(f"Final transcription: '{transcription}'")
                        # Queue the transcription to be broadcast by the main thread
                        self.manager.queue_transcription(transcription)
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
