import asyncio
import queue
import threading
import time
import numpy as np
import pyaudio
import whisper
import tempfile
import os
from pathlib import Path
from .base_service import BaseTranscriptionService

# --- Configuration ---
MODEL_SIZE = "base"  # "tiny", "base", "small", "medium", "large"
SAMPLE_RATE = 16000
CHUNK_DURATION_S = 1.0
CHUNK_SAMPLES = int(SAMPLE_RATE * CHUNK_DURATION_S)
CHANNELS = 1
AUDIO_FORMAT = pyaudio.paInt16

# --- VAD Configuration ---
SILENCE_THRESHOLD = 300  # RMS energy threshold for silence
SILENCE_DURATION_S = 0.125  # How many seconds of silence before stopping recording
MIN_RECORDING_DURATION_S = 1.0  # Minimum recording duration to avoid very short clips


class CoreMLTranscriptionService(BaseTranscriptionService):
    def __init__(self, manager):
        super().__init__(manager)
        self.audio_queue = queue.Queue()
        
        print(f"Loading Whisper model '{MODEL_SIZE}' with CoreML optimization...")
        
        # Load the model - this will automatically use CoreML on Apple Silicon
        try:
            self.model = whisper.load_model(MODEL_SIZE)
            print(f"Whisper model '{MODEL_SIZE}' loaded successfully with CoreML acceleration")
        except Exception as e:
            print(f"Failed to load model: {e}")
            raise
        
        # Create temp directory for audio files
        self.temp_dir = tempfile.mkdtemp()
        print(f"Temporary directory created: {self.temp_dir}")

    def audio_callback(self, in_data, frame_count, time_info, status):
        """Puts audio data into a queue; called by PyAudio."""
        self.audio_queue.put(np.frombuffer(in_data, dtype=np.int16))
        return (None, pyaudio.paContinue)

    def stop(self):
        """Signal the service to stop gracefully."""
        print("Stopping transcription service...")
        self.stop_event.set()
        # Clean up temp directory
        try:
            import shutil
            shutil.rmtree(self.temp_dir)
            print("Temporary directory cleaned up")
        except Exception as e:
            print(f"Error cleaning up temp directory: {e}")

    def save_audio_to_file(self, audio_data, filename):
        """Save audio data to a temporary WAV file for Whisper processing."""
        import wave
        
        filepath = os.path.join(self.temp_dir, filename)
        
        with wave.open(filepath, 'wb') as wav_file:
            wav_file.setnchannels(CHANNELS)
            wav_file.setsampwidth(2)  # 16-bit audio
            wav_file.setframerate(SAMPLE_RATE)
            wav_file.writeframes(audio_data.tobytes())
        
        return filepath

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
        print("Audio stream started. CoreML service is running.")

        recording_counter = 0

        while not self.stop_event.is_set():
            try:
                # --- Phase 1: Listen for Voice Activity ---
                print("Listening for speech...")
                
                # Wait for audio activity
                speech_detected = False
                first_chunk = None
                
                while not speech_detected and not self.stop_event.is_set():
                    try:
                        # Check if STT should be suppressed due to TTS playback
                        if self.manager.is_stt_suppressed():
                            # Skip processing during TTS playback/cooldown
                            try:
                                self.audio_queue.get(timeout=0.1)  # Drain queue
                            except queue.Empty:
                                pass
                            continue
                        
                        audio_chunk = self.audio_queue.get(timeout=1)
                        
                        # Check for voice activity using RMS
                        rms = np.sqrt(np.mean(audio_chunk.astype(np.float32)**2))
                        
                        if rms > SILENCE_THRESHOLD:
                            print(f"Audio activity detected (RMS: {rms:.2f})")
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
                    # Concatenate chunks
                    audio_data = np.concatenate(audio_buffer, axis=0)
                    
                    # Save to temporary WAV file
                    recording_counter += 1
                    temp_filename = f"recording_{recording_counter}.wav"
                    temp_filepath = self.save_audio_to_file(audio_data, temp_filename)
                    
                    print("Transcribing with CoreML acceleration...")
                    start_time = time.time()
                    
                    try:
                        # Use Whisper with CoreML acceleration
                        result = self.model.transcribe(
                            temp_filepath,
                            language="en",
                            verbose=False
                        )
                        
                        transcription_time = time.time() - start_time
                        transcription = result["text"].strip()

                        if transcription:
                            print(f"CoreML transcription ({transcription_time:.2f}s): '{transcription}'")
                            # Queue the transcription to be broadcast by the main thread
                            self.manager.queue_transcription(transcription)
                        else:
                            print("No speech detected in recording.")
                    
                    except Exception as e:
                        print(f"Error during transcription: {e}")
                    
                    finally:
                        # Clean up temporary file
                        try:
                            os.remove(temp_filepath)
                        except Exception as e:
                            print(f"Error removing temp file: {e}")
                            
                else:
                    print("Recording too short, skipping transcription.")

            except Exception as e:
                print(f"An error occurred in the transcription loop: {e}")
                break
        
        # Cleanup
        stream.stop_stream()
        stream.close()
        p.terminate()
        print("CoreML transcription service stopped.")
