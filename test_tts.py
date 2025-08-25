#!/usr/bin/env python3
"""
Quick test script for Piper TTS functionality.
Tests if the TTS service can synthesize speech correctly.
"""

import os
import numpy as np
import wave
import tempfile

try:
    from piper import PiperVoice
    PIPER_AVAILABLE = True
except ImportError:
    print("Piper TTS not available. Install with: pip install piper-tts")
    PIPER_AVAILABLE = False

def test_tts():
    """Test TTS synthesis and save to a WAV file."""
    if not PIPER_AVAILABLE:
        return False
    
    models_dir = "models"
    model_path = os.path.join(models_dir, "en_US-lessac-medium.onnx")
    config_path = os.path.join(models_dir, "en_US-lessac-medium.onnx.json")
    
    if not os.path.exists(model_path) or not os.path.exists(config_path):
        print("Model files not found. Run 'python3 download_models.py' first.")
        return False
    
    print("Loading Piper TTS model...")
    try:
        voice = PiperVoice.load(model_path, config_path)
        print("✓ Model loaded successfully")
    except Exception as e:
        print(f"✗ Failed to load model: {e}")
        return False
    
    test_text = "Hello! This is a test of the Piper text-to-speech system. It should sound clear and natural."
    print(f"Synthesizing: '{test_text}'")
    
    try:
        # Synthesize audio - fix to handle AudioChunk objects properly
        audio_chunks = []
        sample_rate = None
        
        for audio_chunk in voice.synthesize(test_text):
            # Get the actual sample rate from the first chunk
            if sample_rate is None and hasattr(audio_chunk, 'sample_rate'):
                sample_rate = audio_chunk.sample_rate
                print(f"Detected sample rate: {sample_rate} Hz")
            
            # AudioChunk objects have audio_float_array for float32 data
            if hasattr(audio_chunk, 'audio_float_array'):
                audio_data = audio_chunk.audio_float_array
                
                if isinstance(audio_data, np.ndarray) and audio_data.size > 0:
                    # Flatten the array in case it has unexpected dimensions
                    chunk_flat = audio_data.flatten()
                    if chunk_flat.size > 0:
                        audio_chunks.append(chunk_flat)
        
        if not audio_chunks:
            print("✗ No audio generated")
            return False
        
        # Concatenate chunks
        audio_data = np.concatenate(audio_chunks)
        print(f"✓ Generated {len(audio_data)} audio samples")
        
        # Convert to int16 for WAV file
        audio_clipped = np.clip(audio_data, -1.0, 1.0)
        audio_int16 = (audio_clipped * 32767).astype(np.int16)
        
        # Save to temporary WAV file with correct sample rate
        output_file = "test_tts_output.wav"
        actual_sample_rate = sample_rate or 22050  # Default if not detected
        with wave.open(output_file, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(actual_sample_rate)
            wav_file.writeframes(audio_int16.tobytes())
        
        print(f"✓ Audio saved to: {output_file} (sample rate: {actual_sample_rate} Hz)")
        print("  You can play this file to test the audio quality")
        
        return True
        
    except Exception as e:
        print(f"✗ Error during synthesis: {e}")
        return False

if __name__ == "__main__":
    print("Piper TTS Test")
    print("=" * 20)
    
    success = test_tts()
    
    if success:
        print("\n✓ TTS test completed successfully!")
        print("The TTS service should work correctly with the main application.")
    else:
        print("\n✗ TTS test failed!")
        print("Please check the installation and model files.")
