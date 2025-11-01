"""
STT-Only Test (No TTS)

Test continuous STT without any TTS interference.
"""

from speech_agent_integration import SpeechEnabledAgent
import time

def stt_only_handler(text):
    """Handle speech without any TTS response."""
    print(f"\n🎤 STT HEARD: \"{text}\"")
    print("📝 (No TTS response - testing STT only)")
    return None  # No TTS response

def main():
    print("🔍 STT-Only Continuous Test")
    print("- No TTS responses (to eliminate TTS interference)")
    print("- Testing if STT works continuously")
    print("- Say multiple things and watch for 🎤 messages")
    
    agent = SpeechEnabledAgent()
    agent.set_transcription_handler(stt_only_handler)
    
    print("\nStarting STT-only test...")
    agent.start_listening()
    
    try:
        for i in range(60):
            time.sleep(1)
            if i % 10 == 0:
                print(f"[{i}s] Ready for speech...")
    except KeyboardInterrupt:
        print("\nStopping...")
        agent.stop_listening()

if __name__ == "__main__":
    main()
