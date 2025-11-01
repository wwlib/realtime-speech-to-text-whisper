"""
Speech Integration Module for Chat Agents

This module provides a simplified interface for integrating STT and TTS
capabilities into chat-based agents without the WebSocket/FastAPI overhead.
"""

import asyncio
import threading
import queue
import time
from typing import Callable, Optional, Dict, Any

from stt.service_factory import create_stt_service
from tts.tts_service import TTSService


class SpeechAgentManager:
    """Simplified manager for agent integration without WebSocket dependencies."""
    
    def __init__(self):
        self.active_connections = {}  # Dummy for compatibility
        self.client_settings = {}
        self.transcription_queue = queue.Queue()
        
        # Audio ducking for feedback prevention
        self.tts_active = threading.Event()
        self.tts_end_time = 0
        self.tts_cooldown_seconds = 0.5  # Reduced from 1.0 to 0.5 seconds
        self._lock = threading.Lock()
        
        # Recent TTS text tracking
        self.recent_tts_texts = []
        self.max_recent_tts = 10
        
        # Callback for when transcription is ready
        self.transcription_callback: Optional[Callable[[str], None]] = None
    
    def set_transcription_callback(self, callback: Callable[[str], None]):
        """Set callback function to handle new transcriptions."""
        self.transcription_callback = callback
    
    def queue_transcription(self, transcription: str):
        """Queue a transcription for processing."""
        self.transcription_queue.put(transcription)
        
        # Immediately call callback if set
        if self.transcription_callback:
            try:
                self.transcription_callback(transcription)
            except Exception as e:
                print(f"Error in transcription callback: {e}")
    
    # Copy all the audio ducking and feedback prevention methods from ConnectionManager
    def start_tts_playback(self):
        """Signal that TTS playback is starting."""
        with self._lock:
            self.tts_active.set()
            print("TTS playback started - STT sensitivity reduced")
    
    def end_tts_playback(self):
        """Signal that TTS playback has ended."""
        with self._lock:
            self.tts_active.clear()
            self.tts_end_time = time.time()
            print(f"TTS playback ended - STT will resume in {self.tts_cooldown_seconds}s")
    
    def is_stt_suppressed(self):
        """Check if STT should be suppressed due to TTS playback."""
        with self._lock:
            if self.tts_active.is_set():
                return True
            
            if self.tts_end_time > 0:
                time_since_tts_end = time.time() - self.tts_end_time
                if time_since_tts_end < self.tts_cooldown_seconds:
                    return True
                else:
                    self.tts_end_time = 0
            
            return False
    
    def add_recent_tts_text(self, text: str):
        """Add text to recent TTS list for feedback prevention."""
        with self._lock:
            self.recent_tts_texts.append(text.lower().strip())
            if len(self.recent_tts_texts) > self.max_recent_tts:
                self.recent_tts_texts.pop(0)
    
    def is_text_similar_to_recent_tts(self, text: str, similarity_threshold: float = 0.8) -> bool:
        """Check if transcribed text is similar to recently spoken TTS text."""
        if not text.strip():
            return False
            
        text_lower = text.lower().strip()
        
        with self._lock:
            for recent_tts in self.recent_tts_texts:
                if self._simple_similarity(text_lower, recent_tts) > similarity_threshold:
                    print(f"Filtered potential feedback: '{text}' similar to recent TTS: '{recent_tts}'")
                    return True
        return False
    
    def _simple_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple similarity between two texts."""
        if not text1 or not text2:
            return 0.0
        
        if text1 in text2 or text2 in text1:
            return 1.0
        
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return 0.0
            
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    # Dummy methods for TTS service compatibility
    async def broadcast_to_client(self, message, client_id=None):
        """Dummy method for TTS service compatibility."""
        pass


class SimpleTTSService:
    """Simplified TTS service for agent integration."""
    
    def __init__(self, manager: SpeechAgentManager):
        self.manager = manager
        self.stop_event = threading.Event()
        self.voice = None
        
        # Load Piper voice
        from pathlib import Path
        try:
            from piper import PiperVoice
            models_dir = Path(__file__).parent / "tts" / "models"
            model_path = models_dir / "en_US-amy-medium.onnx"
            config_path = models_dir / "en_US-amy-medium.onnx.json"
            
            if model_path.exists() and config_path.exists():
                self.voice = PiperVoice.load(str(model_path), str(config_path))
                print(f"TTS voice loaded successfully")
            else:
                print("TTS models not found. Run 'python tts/download_models.py'")
                self.voice = None
        except ImportError:
            print("Piper TTS not installed. Run: pip install piper-tts")
            self.voice = None
    
    def synthesize_and_play(self, text: str) -> bool:
        """Synthesize speech and play it using system audio to avoid PyAudio interference."""
        if not self.voice:
            print("No voice model loaded")
            return False
        
        try:
            import numpy as np
            import wave
            import os
            import subprocess
            import tempfile
            
            # Add to recent TTS for feedback prevention
            self.manager.add_recent_tts_text(text)
            
            # Signal TTS start
            self.manager.start_tts_playback()
            
            # Synthesize audio
            audio_chunks = []
            sample_rate = None
            
            for audio_chunk in self.voice.synthesize(text):
                if sample_rate is None and hasattr(audio_chunk, 'sample_rate'):
                    sample_rate = audio_chunk.sample_rate
                
                if hasattr(audio_chunk, 'audio_float_array'):
                    audio_data = audio_chunk.audio_float_array
                    if isinstance(audio_data, np.ndarray) and audio_data.size > 0:
                        audio_chunks.append(audio_data.flatten())
            
            if audio_chunks:
                # Concatenate and convert to int16
                audio_data = np.concatenate(audio_chunks)
                audio_clipped = np.clip(audio_data, -1.0, 1.0)
                audio_int16 = (audio_clipped * 32767).astype(np.int16)
                
                # Write to temporary WAV file and play with system audio
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                    temp_path = temp_file.name
                
                try:
                    # Write WAV file
                    with wave.open(temp_path, "wb") as wav_file:
                        wav_file.setnchannels(1)  # Mono
                        wav_file.setsampwidth(2)  # 16-bit
                        wav_file.setframerate(sample_rate or 22050)
                        wav_file.writeframes(audio_int16.tobytes())
                    
                    # Play using system audio player (completely isolated from PyAudio)
                    if os.uname().sysname == 'Darwin':  # macOS
                        subprocess.run(['afplay', temp_path], 
                                     stdout=subprocess.DEVNULL, 
                                     stderr=subprocess.DEVNULL,
                                     check=False)
                    elif os.name == 'nt':  # Windows
                        subprocess.run(['powershell', '-c', 
                                      f'(New-Object Media.SoundPlayer "{temp_path}").PlaySync()'],
                                     stdout=subprocess.DEVNULL, 
                                     stderr=subprocess.DEVNULL,
                                     check=False)
                    else:  # Linux
                        subprocess.run(['aplay', temp_path], 
                                     stdout=subprocess.DEVNULL, 
                                     stderr=subprocess.DEVNULL,
                                     check=False)
                    
                    # Signal TTS end immediately after playback
                    self.manager.end_tts_playback()
                    
                    print(f"TTS completed: '{text}'")
                    return True
                    
                finally:
                    # Clean up temp file
                    try:
                        os.unlink(temp_path)
                    except:
                        pass
            
        except Exception as e:
            print(f"TTS error: {e}")
            self.manager.end_tts_playback()
            return False
        
        return False


class SpeechEnabledAgent:
    """Main class for speech-enabled chat agent integration."""
    
    def __init__(self, stt_service_type: str = "auto"):
        self.manager = SpeechAgentManager()
        self.stt_service = None
        self.tts_service = None
        self.stt_thread = None
        self.running = False
        
        # Initialize services
        try:
            self.stt_service = create_stt_service(self.manager, stt_service_type)
            self.tts_service = SimpleTTSService(self.manager)
            print("Speech services initialized successfully")
        except Exception as e:
            print(f"Failed to initialize speech services: {e}")
    
    def set_transcription_handler(self, handler: Callable[[str], str]):
        """
        Set the handler function for processing transcriptions.
        
        Args:
            handler: Function that takes transcribed text and returns agent response
        """
        def transcription_callback(transcription: str):
            # Check for feedback prevention
            if self.manager.is_text_similar_to_recent_tts(transcription):
                print(f"Skipping probable feedback: '{transcription}'")
                return
            
            try:
                # Process with agent
                response = handler(transcription)
                
                # Speak the response if TTS is available
                if response and self.tts_service:
                    # Run TTS in background thread to avoid blocking
                    threading.Thread(
                        target=self.tts_service.synthesize_and_play,
                        args=(response,),
                        daemon=True
                    ).start()
                    
            except Exception as e:
                print(f"Error processing transcription: {e}")
        
        self.manager.set_transcription_callback(transcription_callback)
    
    def start_listening(self):
        """Start the STT service in a background thread."""
        if not self.stt_service:
            print("STT service not available")
            return False
        
        if self.running:
            print("Speech services already running")
            return True
        
        self.running = True
        
        # Start STT in background thread
        loop = asyncio.new_event_loop()
        self.stt_thread = threading.Thread(
            target=self._run_stt_service,
            args=(loop,),
            daemon=True
        )
        self.stt_thread.start()
        
        print("Speech-enabled agent started listening...")
        return True
    
    def _run_stt_service(self, loop):
        """Run STT service in background thread."""
        asyncio.set_event_loop(loop)
        self.stt_service.run(loop)
    
    def stop_listening(self):
        """Stop the STT service."""
        if self.stt_service and self.running:
            self.stt_service.stop()
            self.running = False
            print("Speech services stopped")
    
    def speak(self, text: str):
        """Speak text using TTS."""
        if self.tts_service:
            # Run in background thread
            threading.Thread(
                target=self.tts_service.synthesize_and_play,
                args=(text,),
                daemon=True
            ).start()
        else:
            print(f"TTS not available. Would speak: '{text}'")
