#!/usr/bin/env python3
"""
Simple demo of the TTS service without the full web server.
Useful for testing TTS functionality quickly.
"""

import asyncio
import sys

# Mock manager class for standalone testing
class MockManager:
    async def broadcast_to_client(self, message, client_id=None):
        print(f"[MOCK] Would send to client: {message}")

async def demo_tts():
    """Demo the TTS service with some sample text."""
    from tts_service import TTSService
    
    # Create mock manager and TTS service
    manager = MockManager()
    tts = TTSService(manager)
    
    if not tts.voice:
        print("TTS service not available. Please run 'python3 download_models.py' first.")
        return
    
    # Test texts
    test_texts = [
        "Hello! This is a test of the text-to-speech system.",
        "The quick brown fox jumps over the lazy dog.",
        "Realtime speech-to-text with text-to-speech is now working!",
        "This voice synthesis is powered by Piper TTS."
    ]
    
    print("TTS Demo - Testing voice synthesis...")
    print("=" * 50)
    
    for i, text in enumerate(test_texts, 1):
        print(f"\nTest {i}: '{text}'")
        
        # Synthesize audio
        result = tts.synthesize_audio(text)
        
        if result[0] is not None:
            audio_data, sample_rate = result
            print(f"  ✓ Generated {len(audio_data)} audio samples at {sample_rate}Hz")
            
            # Save to file for manual testing
            import wave
            filename = f"demo_output_{i}.wav"
            with wave.open(filename, 'wb') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(audio_data.tobytes())
            print(f"  ✓ Saved to: {filename}")
        else:
            print(f"  ✗ Failed to generate audio")
    
    print(f"\nDemo complete! Generated {len(test_texts)} audio files.")
    print("You can play these WAV files to test the voice quality.")

if __name__ == "__main__":
    try:
        asyncio.run(demo_tts())
    except KeyboardInterrupt:
        print("\nDemo interrupted by user.")
    except Exception as e:
        print(f"Demo failed: {e}")
        sys.exit(1)
