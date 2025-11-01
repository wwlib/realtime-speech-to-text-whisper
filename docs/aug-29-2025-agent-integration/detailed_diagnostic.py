"""
Advanced STT Diagnostic with Detailed Timing

This will help us understand exactly what's happening with the audio ducking.
"""

from speech_agent_integration import SpeechEnabledAgent
import time
import threading

class DetailedDiagnostic:
    def __init__(self):
        self.agent = SpeechEnabledAgent()
        self.agent.set_transcription_handler(self.handle_speech)
        self.speech_count = 0
        
    def handle_speech(self, text):
        self.speech_count += 1
        print(f"\n🎤 [{self.speech_count}] STT HEARD: \"{text}\"")
        print(f"    Time: {time.strftime('%H:%M:%S')}")
        
        if self.speech_count == 1:
            response = "I heard you. Say something else in 3 seconds."
            print(f"🔊 TTS RESPONSE: \"{response}\"")
            return response
        else:
            print(f"🔇 Silent response (no TTS)")
            return None
    
    def monitor_stt_status(self):
        """Monitor STT suppression status in background."""
        while True:
            try:
                suppressed = self.agent.manager.is_stt_suppressed()
                tts_active = self.agent.manager.tts_active.is_set()
                
                # Only print when status changes
                current_time = time.time()
                status = f"{'SUPPRESSED' if suppressed else 'LISTENING'}"
                
                if hasattr(self, '_last_status') and self._last_status != status:
                    print(f"⚡ [{time.strftime('%H:%M:%S')}] STT Status Changed: {status}")
                    if suppressed and not tts_active:
                        # Check cooldown details
                        time_since_end = current_time - self.agent.manager.tts_end_time if self.agent.manager.tts_end_time > 0 else 0
                        print(f"   Cooldown remaining: {max(0, self.agent.manager.tts_cooldown_seconds - time_since_end):.1f}s")
                
                self._last_status = status
                time.sleep(0.1)
            except Exception as e:
                print(f"Monitor error: {e}")
                break
    
    def run(self):
        print("🔍 Advanced STT Diagnostic")
        print("- First speech gets TTS response")
        print("- Subsequent speech gets no TTS (to test pure STT)")
        print("- Monitoring STT status changes in real-time")
        print("- Watch for status changes after TTS\n")
        
        # Start status monitor in background
        monitor_thread = threading.Thread(target=self.monitor_stt_status, daemon=True)
        monitor_thread.start()
        
        self.agent.start_listening()
        
        try:
            for i in range(60):
                time.sleep(1)
                if i % 15 == 0:
                    suppressed = self.agent.manager.is_stt_suppressed()
                    status = "SUPPRESSED" if suppressed else "LISTENING"
                    print(f"[{i}s] Current STT Status: {status}")
        except KeyboardInterrupt:
            print("\nStopping diagnostic...")
            self.agent.stop_listening()

if __name__ == "__main__":
    diagnostic = DetailedDiagnostic()
    diagnostic.run()
