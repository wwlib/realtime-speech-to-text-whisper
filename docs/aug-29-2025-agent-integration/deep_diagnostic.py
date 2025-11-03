"""
Deep STT Loop Diagnostic

This will trace exactly what happens in the transcription loop after TTS.
"""

import time
import threading
from speech_agent_integration import SpeechEnabledAgent

class DeepDiagnostic:
    def __init__(self):
        self.agent = SpeechEnabledAgent()
        self.agent.set_transcription_handler(self.handle_speech)
        self.speech_count = 0
        
        # Patch the transcription service to add debug logging
        original_run = self.agent.stt_service.run
        self.agent.stt_service.run = self.patched_run
        
    def handle_speech(self, text):
        self.speech_count += 1
        print(f"\n🎤 [{self.speech_count}] STT HEARD: \"{text}\"")
        
        if self.speech_count == 1:
            response = "I heard you. Now testing if I can hear you again."
            print(f"🔊 TTS: \"{response}\"")
            return response
        else:
            print(f"🔇 No TTS - just testing STT")
            return None
    
    def patched_run(self, loop):
        """Patched version of the transcription service run method with debug logging."""
        import asyncio
        import pyaudio
        import numpy as np
        import queue
        
        asyncio.set_event_loop(loop)
        p = pyaudio.PyAudio()

        try:
            print("🔧 Opening audio stream...")
            stream = p.open(
                format=self.agent.stt_service.audio_queue.__class__.__module__.split('.')[0] == 'pyaudio' and pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                frames_per_buffer=16000,
                stream_callback=self.agent.stt_service.audio_callback,
                input_device_index=None
            )
        except Exception as e:
            print(f"❌ Audio stream error: {e}")
            p.terminate()
            return

        stream.start_stream()
        print("✅ Audio stream started")

        iteration = 0
        while not self.agent.stt_service.stop_event.is_set():
            iteration += 1
            try:
                print(f"\n[LOOP {iteration}] === Starting iteration ===")
                
                # Phase 1: Listen for Voice Activity
                print("[LOOP] Phase 1: Listening for voice activity...")
                
                speech_detected = False
                first_chunk = None
                
                phase1_attempts = 0
                while not speech_detected and not self.agent.stt_service.stop_event.is_set():
                    phase1_attempts += 1
                    try:
                        # Check suppression status
                        suppressed = self.agent.stt_service.manager.is_stt_suppressed()
                        if suppressed:
                            print(f"[LOOP] Phase 1 - Attempt {phase1_attempts}: STT SUPPRESSED - clearing queue")
                            queue_size_before = self.agent.stt_service.audio_queue.qsize()
                            while not self.agent.stt_service.audio_queue.empty():
                                try:
                                    self.agent.stt_service.audio_queue.get_nowait()
                                except queue.Empty:
                                    break
                            if queue_size_before > 0:
                                print(f"[LOOP] Cleared {queue_size_before} chunks during suppression")
                            time.sleep(0.1)
                            continue
                        
                        print(f"[LOOP] Phase 1 - Attempt {phase1_attempts}: Waiting for audio (queue size: {self.agent.stt_service.audio_queue.qsize()})")
                        audio_chunk = self.agent.stt_service.audio_queue.get(timeout=1)
                        
                        # Check for voice activity
                        rms = np.sqrt(np.mean(audio_chunk.astype(np.float32)**2))
                        print(f"[LOOP] Phase 1 - Got audio chunk, RMS: {rms:.1f}")
                        
                        if rms > 200:  # Using our adjusted threshold
                            print(f"[LOOP] Phase 1 - RMS above threshold, testing with Whisper...")
                            audio_float = audio_chunk.astype(np.float32) / 32768.0
                            segments, _ = self.agent.stt_service.model.transcribe(
                                audio_float,
                                language="en",
                                vad_filter=True,
                                vad_parameters=dict(min_silence_duration_ms=300),
                            )
                            
                            transcription = "".join(segment.text for segment in segments).strip()
                            
                            if transcription:
                                print(f"[LOOP] Phase 1 - SPEECH DETECTED: '{transcription}'")
                                speech_detected = True
                                first_chunk = audio_chunk
                            else:
                                print(f"[LOOP] Phase 1 - No speech in transcription")
                        else:
                            print(f"[LOOP] Phase 1 - RMS too low, continuing...")
                    
                    except queue.Empty:
                        print(f"[LOOP] Phase 1 - Attempt {phase1_attempts}: Queue timeout")
                        continue
                    except Exception as e:
                        print(f"[LOOP] Phase 1 - Error: {e}")
                        continue
                
                if self.agent.stt_service.stop_event.is_set():
                    print("[LOOP] Stop event set, breaking")
                    break

                if not speech_detected:
                    print("[LOOP] Phase 1 - No speech detected, restarting loop")
                    continue

                print("[LOOP] Phase 2: Recording speech...")
                # Simplified phase 2 - just queue the transcription
                if first_chunk is not None:
                    self.agent.stt_service.manager.queue_transcription("Test transcription from deep diagnostic")
                
                print("[LOOP] === End iteration ===")
                
                # Add a small delay to prevent overwhelming output
                time.sleep(0.5)

            except Exception as e:
                print(f"[LOOP] Error in main loop: {e}")
                break
        
        # Cleanup
        stream.stop_stream()
        stream.close()
        p.terminate()
        print("🔧 Transcription service stopped")
    
    def run(self):
        print("🔍 Deep STT Loop Diagnostic")
        print("- Traces every step of the transcription loop")
        print("- Shows exactly where the loop gets stuck")
        print("- First speech gets TTS, then watch the loop behavior\n")
        
        print("Starting deep diagnostic...")
        self.agent.start_listening()
        
        try:
            for i in range(60):
                time.sleep(1)
                if i % 10 == 0:
                    print(f"\n[MAIN] {i}s elapsed - STT loop should be running...")
        except KeyboardInterrupt:
            print("\nStopping diagnostic...")
            self.agent.stop_listening()

if __name__ == "__main__":
    diagnostic = DeepDiagnostic()
    diagnostic.run()
