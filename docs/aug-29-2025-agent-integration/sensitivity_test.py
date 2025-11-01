"""
Speech Detection Sensitivity Test

This will help us understand if STT is detecting speech attempts after TTS.
"""

from speech_agent_integration import SpeechEnabledAgent
import time

class SensitivityTest:
    def __init__(self):
        self.agent = SpeechEnabledAgent()
        self.agent.set_transcription_handler(self.handle_speech)
        self.speech_count = 0
        
    def handle_speech(self, text):
        self.speech_count += 1
        print(f"\n🎤 [{self.speech_count}] STT HEARD: \"{text}\"")
        
        if self.speech_count == 1:
            response = "I heard you. Now I will be silent. Try speaking again."
            print(f"🔊 TTS: \"{response}\"")
            return response
        else:
            print(f"🔇 No TTS - just testing STT detection")
            return None
    
    def run(self):
        print("🔊 Speech Detection Sensitivity Test")
        print("=" * 50)
        print("INSTRUCTIONS:")
        print("1. Say something first (you'll get a TTS response)")
        print("2. Wait for TTS to finish")
        print("3. Try speaking multiple times with different volumes")
        print("4. Watch for 'Speech detected' messages")
        print("5. If you see 'Speech detected' but no transcription,")
        print("   it means the recording is too short")
        print("\nStarting test...\n")
        
        self.agent.start_listening()
        
        try:
            for i in range(90):  # 90 seconds
                time.sleep(1)
                if i % 15 == 0:
                    suppressed = self.agent.manager.is_stt_suppressed()
                    if not suppressed:
                        print(f"[{i}s] 🎧 Ready for speech - try speaking now")
                    else:
                        print(f"[{i}s] 🔇 STT suppressed (TTS playing)")
        except KeyboardInterrupt:
            print("\nStopping test...")
            self.agent.stop_listening()

if __name__ == "__main__":
    test = SensitivityTest()
    test.run()
