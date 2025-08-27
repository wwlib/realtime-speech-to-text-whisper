import asyncio
import threading
import queue
import numpy as np
import tempfile
import os
from pathlib import Path

try:
    from piper import PiperVoice
except ImportError:
    print("Piper TTS not installed. Run: pip install piper-tts")
    PiperVoice = None

class TTSService:
    def __init__(self, manager):
        self.manager = manager
        self.tts_queue = queue.Queue()
        self.stop_event = threading.Event()
        self.voice = None
        
        # Piper voice model paths - use models relative to tts folder
        self.models_dir = Path(__file__).parent / "models"
        self.model_path = self.models_dir / "en_US-amy-medium.onnx"
        self.config_path = self.models_dir / "en_US-amy-medium.onnx.json"
        
        self.load_voice()
    
    def load_voice(self):
        """Load the Piper voice model."""
        if not PiperVoice:
            print("Piper TTS not available. Install with: pip install piper-tts")
            return
            
        try:
            if self.model_path.exists() and self.config_path.exists():
                self.voice = PiperVoice.load(str(self.model_path), str(self.config_path))
                print(f"Piper TTS voice loaded successfully from {self.model_path}")
            else:
                print(f"Voice model not found at {self.model_path}")
                print("Run 'python tts/download_models.py' to download the required TTS models")
                self.voice = None
        except Exception as e:
            print(f"Failed to load Piper voice: {e}")
            self.voice = None
    
    def synthesize_audio(self, text):
        """Synthesize speech from text using Piper."""
        if not self.voice:
            print("No voice model loaded, cannot synthesize speech")
            return None
        
        try:
            # Piper outputs audio as a generator of AudioChunk objects
            audio_chunks = []
            sample_rate = None
            
            for audio_chunk in self.voice.synthesize(text):
                # Get the actual sample rate from the first chunk
                if sample_rate is None and hasattr(audio_chunk, 'sample_rate'):
                    sample_rate = audio_chunk.sample_rate
                    print(f"Piper sample rate: {sample_rate} Hz")
                
                # AudioChunk objects have audio_float_array for float32 data
                if hasattr(audio_chunk, 'audio_float_array'):
                    audio_data = audio_chunk.audio_float_array
                    
                    if isinstance(audio_data, np.ndarray) and audio_data.size > 0:
                        # Flatten the array in case it has unexpected dimensions
                        chunk_flat = audio_data.flatten()
                        if chunk_flat.size > 0:
                            audio_chunks.append(chunk_flat)
                    
            if audio_chunks:
                # Concatenate all chunks
                audio_data = np.concatenate(audio_chunks)
                
                # Convert to int16 for streaming (Piper outputs float32)
                # Ensure we don't clip the audio
                audio_clipped = np.clip(audio_data, -1.0, 1.0)
                audio_int16 = (audio_clipped * 32767).astype(np.int16)
                
                # Return both audio data and sample rate
                return audio_int16, sample_rate or 22050  # Default to 22050 if not detected
            else:
                print("No valid audio chunks generated")
                return None, None
                
        except Exception as e:
            print(f"Error synthesizing speech: {e}")
            import traceback
            traceback.print_exc()
            return None, None
    
    async def process_tts_request(self, text, client_id=None, auto_tts=False):
        """Process a TTS request and stream audio to client(s)."""
        tts_type = "Auto-TTS" if auto_tts else "Manual TTS"
        print(f"Processing {tts_type} request: '{text}'")
        
        # Synthesize audio (this runs in a thread to avoid blocking)
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self.synthesize_audio, text)
        
        if result[0] is not None:
            audio_data, sample_rate = result
            await self.stream_audio(audio_data, sample_rate, client_id, auto_tts)
        else:
            print("Failed to synthesize audio")
    
    async def stream_audio(self, audio_data, sample_rate, client_id=None, auto_tts=False):
        """Stream audio data to browser client(s) in chunks."""
        chunk_size = int(sample_rate * 0.2)  # ~0.2 seconds worth of samples
        total_chunks = len(audio_data) // chunk_size + (1 if len(audio_data) % chunk_size else 0)
        
        tts_type = "Auto-TTS" if auto_tts else "Manual TTS"
        print(f"Streaming {len(audio_data)} audio samples at {sample_rate}Hz in {total_chunks} chunks ({tts_type})")
        
        # Send audio start signal with correct sample rate and auto-TTS flag
        await self.manager.broadcast_to_client({
            "type": "tts_start",
            "sample_rate": sample_rate,
            "channels": 1,
            "total_chunks": total_chunks,
            "auto_tts": auto_tts
        }, client_id)
        
        # Stream audio chunks
        for i in range(0, len(audio_data), chunk_size):
            chunk = audio_data[i:i+chunk_size]
            
            # Convert numpy array to bytes
            audio_bytes = chunk.tobytes()
            
            await self.manager.broadcast_to_client({
                "type": "tts_audio",
                "audio_data": audio_bytes.hex(),  # Convert to hex string for JSON
                "chunk_index": i // chunk_size
            }, client_id)
            
            # Small delay to prevent overwhelming the client
            await asyncio.sleep(0.01)
        
        # Send audio end signal
        await self.manager.broadcast_to_client({
            "type": "tts_end"
        }, client_id)
        
        print("Audio streaming complete")
    
    def stop(self):
        """Stop the TTS service."""
        self.stop_event.set()
