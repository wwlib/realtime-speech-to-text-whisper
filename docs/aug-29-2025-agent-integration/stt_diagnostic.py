"""
STT Diagnostic Tool

This helps debug why STT stops working after the first response.
"""

from speech_agent_integration import SpeechEnabledAgent
import time
import threading

class DiagnosticAgent:
    def __init__(self):
        self.agent = SpeechEnabledAgent()
        self.agent.set_transcription_handler(self.handle_speech)
        self.speech_count = 0
        
    def handle_speech(self, text):
        self.speech_count += 1
        print(f"\n🎤 [{self.speech_count}] STT HEARD: \"{text}\"")
        
        if self.speech_count == 1:
            # First time - respond with TTS
            response = f"I heard you say: {text}. Try saying something else."
            print(f"🔊 RESPONDING: \"{response}\"")
            return response
        else:
            # Subsequent times - no TTS to avoid interference
            print(f"🔇 NOT RESPONDING (to test STT without TTS interference)")
            return None  # No TTS response
    
    def run_diagnostic(self):
        print("🔍 STT Diagnostic Mode")
        print("- First utterance will get a TTS response")
        print("- Subsequent utterances will be silent (to test STT only)")
        print("- This helps isolate if TTS is interfering with STT")
        print("\nStarting diagnostic...")
        
        self.agent.start_listening()
        
        try:
            for i in range(60):
                time.sleep(1)
                if i % 10 == 0:
                    status = "listening..." if self.agent.manager.is_stt_suppressed() == False else "suppressed..."
                    print(f"[{i}s] STT status: {status}")
        except KeyboardInterrupt:
            print("\nStopping diagnostic...")
            self.agent.stop_listening()

if __name__ == "__main__":
    diagnostic = DiagnosticAgent()
    diagnostic.run_diagnostic()
