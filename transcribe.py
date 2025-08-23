import queue
import threading
import time
import numpy as np
import pyaudio
from faster_whisper import WhisperModel

# --- Configuration ---
# Whisper Model
MODEL_SIZE = "base.en"  # Options: "tiny.en", "base.en", "small.en", "medium.en"
COMPUTE_TYPE = "int8"
DEVICE = "cpu"

# Audio Stream
SAMPLE_RATE = 16000
CHUNK_DURATION_S = 1.0  # Process audio in 1-second chunks
CHUNK_SAMPLES = int(SAMPLE_RATE * CHUNK_DURATION_S)
CHANNELS = 1
AUDIO_FORMAT = pyaudio.paInt16

# Wake Phrases
WAKE_PHRASES = ["hey robo", "hey, robo", "hey robot", "hey, robot"]
# How long to record after the wake phrase is detected
RECORD_AFTER_WAKE_S = 5

# VAD (Voice Activity Detection)
SILENCE_THRESHOLD = 300  # RMS energy threshold for silence. Adjust this based on your microphone sensitivity.
SILENCE_DURATION_S = 2.0 # How many seconds of silence to wait for before stopping.

# --- Global State ---
audio_queue = queue.Queue()
stop_event = threading.Event()
wake_phrase_detected = threading.Event()

def audio_callback(in_data, frame_count, time_info, status):
    """Puts audio data into a queue; called by PyAudio."""
    audio_queue.put(np.frombuffer(in_data, dtype=np.int16))
    return (None, pyaudio.paContinue)

def transcription_thread():
    """
    Continuously transcribes audio from the queue and listens for a wake phrase.
    Once the wake phrase is detected, it records and transcribes the following audio.
    """
    print("Transcription thread started.")
    model = WhisperModel(MODEL_SIZE, device=DEVICE, compute_type=COMPUTE_TYPE)

    while not stop_event.is_set():
        try:
            # --- Phase 1: Listen for Wake Phrase ---
            print("\nListening for wake phrase...")
            
            # Continuously transcribe and check for the wake phrase
            while not wake_phrase_detected.is_set():
                if stop_event.is_set():
                    break
                
                # Get a chunk of audio
                audio_chunk = audio_queue.get(timeout=1)
                audio_float = audio_chunk.astype(np.float32) / 32768.0

                # Transcribe the chunk
                segments, _ = model.transcribe(
                    audio_float,
                    language="en",
                    vad_filter=True,
                    vad_parameters=dict(min_silence_duration_ms=500),
                )
                
                transcription = "".join(segment.text for segment in segments).lower().strip()

                if transcription:
                    print(f"Heard: '{transcription}'")

                # Check if any wake phrase is in the transcription
                for phrase in WAKE_PHRASES:
                    if phrase in transcription:
                        print(f"\n--- Wake phrase '{phrase}' detected! ---")
                        wake_phrase_detected.set()
                        break  # Exit loop once a phrase is detected

            if stop_event.is_set():
                break

            # --- Phase 2: Record based on Voice Activity ---
            print("Recording command (waiting for silence to stop)...")
            
            audio_buffer = []
            silence_start_time = None
            
            # Drain the queue of any old audio
            while not audio_queue.empty():
                audio_queue.get_nowait()

            while True:
                if stop_event.is_set():
                    break
                
                try:
                    audio_chunk = audio_queue.get(timeout=0.5)
                    audio_buffer.append(audio_chunk)

                    # Simple RMS-based VAD
                    rms = np.sqrt(np.mean(audio_chunk.astype(np.float32)**2))

                    if rms < SILENCE_THRESHOLD:
                        if silence_start_time is None:
                            silence_start_time = time.time()
                        elif time.time() - silence_start_time > SILENCE_DURATION_S:
                            print("\nSilence detected, stopping recording.")
                            break
                    else:
                        # Reset silence timer if speech is detected
                        silence_start_time = None
                        print("Recording...", end='\r')


                except queue.Empty:
                    # If the queue is empty, check the silence timer
                    if silence_start_time and (time.time() - silence_start_time > SILENCE_DURATION_S):
                        print("\nSilence detected after timeout, stopping recording.")
                        break
                    continue
            
            print("\nRecording complete.")

            if stop_event.is_set() or not audio_buffer:
                wake_phrase_detected.clear()
                continue

            # Concatenate chunks and transcribe the full command
            audio_data = np.concatenate(audio_buffer, axis=0)
            audio_float = audio_data.astype(np.float32) / 32768.0

            print("Transcribing command...")
            segments, _ = model.transcribe(audio_float, language="en")
            
            final_transcription = " ".join(segment.text for segment in segments).strip()

            if final_transcription:
                print(f"\nFinal Transcription: {final_transcription}")
                # Here you would send the transcription to your LLM
                # e.g., send_to_ollama(final_transcription)
            else:
                print("No command was transcribed.")

            # Reset for the next wake phrase
            wake_phrase_detected.clear()

        except queue.Empty:
            # This is expected if no audio is received for a moment
            continue
        except Exception as e:
            print(f"An error occurred in the transcription thread: {e}")
            break

    print("Transcription thread stopped.")


def main():
    """Main function to set up and run the application."""
    p = pyaudio.PyAudio()

    try:
        stream = p.open(
            format=AUDIO_FORMAT,
            channels=CHANNELS,
            rate=SAMPLE_RATE,
            input=True,
            frames_per_buffer=CHUNK_SAMPLES,
            stream_callback=audio_callback,
        )
    except OSError as e:
        print(f"Error opening audio stream: {e}")
        print("Please ensure you have a working microphone connected.")
        p.terminate()
        return

    # Start the transcription thread
    t_thread = threading.Thread(target=transcription_thread, daemon=True)
    t_thread.start()

    # Start the audio stream
    stream.start_stream()

    try:
        # Keep the main thread alive until Ctrl+C is pressed
        while t_thread.is_alive():
            t_thread.join(timeout=1)
    except KeyboardInterrupt:
        print("\nStopping application...")
        stop_event.set()
        # Unblock any waiting queue.get() calls
        audio_queue.put(np.zeros(CHUNK_SAMPLES, dtype=np.int16))
        wake_phrase_detected.set() # Ensure the inner loop exits

    # Wait for the transcription thread to finish
    t_thread.join()

    # Clean up
    stream.stop_stream()
    stream.close()
    p.terminate()

    print("Application stopped.")

if __name__ == "__main__":
    main()
