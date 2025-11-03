import queue
import threading
import time
from fastapi import WebSocket


class ConnectionManager:
    """Manages WebSocket connections and transcription queue for thread-safe communication"""
    
    def __init__(self):
        self.active_connections: dict[WebSocket, str] = {}
        self.client_settings: dict[str, dict] = {}  # Track client settings including auto-TTS
        self.transcription_queue = queue.Queue()  # For thread-safe communication between STT and main
        
        # Audio ducking for feedback prevention
        self.tts_active = threading.Event()
        self.tts_end_time = 0
        self.tts_cooldown_seconds = 1.0  # Wait 1 second after TTS ends before resuming STT
        self._lock = threading.Lock()
        
        # Recent TTS text tracking for feedback prevention
        self.recent_tts_texts = []  # Store recent TTS texts to avoid re-speaking them
        self.max_recent_tts = 10  # Keep last 10 TTS texts

    async def connect(self, websocket: WebSocket, client_id: str = None):
        await websocket.accept()
        
        # Generate client_id if not provided
        if client_id is None:
            import uuid
            client_id = str(uuid.uuid4())
        
        self.active_connections[websocket] = client_id
        # Initialize client settings with auto-TTS enabled by default
        self.client_settings[client_id] = {"auto_tts_enabled": True}
        print(f"Client {client_id} connected")
        return client_id

    def disconnect(self, websocket: WebSocket):
        client_id = self.active_connections.pop(websocket, "unknown")
        # Clean up client settings
        self.client_settings.pop(client_id, None)
        print(f"Client {client_id} disconnected")

    def update_client_settings(self, client_id: str, settings: dict):
        """Update settings for a specific client."""
        if client_id in self.client_settings:
            self.client_settings[client_id].update(settings)

    def get_client_settings(self, client_id: str):
        """Get settings for a specific client."""
        return self.client_settings.get(client_id, {})

    def queue_transcription(self, transcription: str):
        """Queue a transcription for broadcast to clients (thread-safe)."""
        self.transcription_queue.put(transcription)

    async def process_transcription_queue(self):
        """Process queued transcriptions and broadcast to clients."""
        try:
            while not self.transcription_queue.empty():
                transcription = self.transcription_queue.get_nowait()
                await self.broadcast(transcription)
        except queue.Empty:
            pass

    def set_auto_tts(self, client_id: str, enabled: bool):
        """Set auto-TTS setting for a specific client."""
        if client_id in self.client_settings:
            self.client_settings[client_id]["auto_tts_enabled"] = enabled
            print(f"Client {client_id} auto-TTS: {'enabled' if enabled else 'disabled'}")

    def is_auto_tts_enabled(self, client_id: str) -> bool:
        """Check if auto-TTS is enabled for a specific client."""
        return self.client_settings.get(client_id, {}).get("auto_tts_enabled", True)

    def set_auto_tts(self, client_id: str, enabled: bool):
        """Set auto-TTS setting for a specific client."""
        if client_id in self.client_settings:
            self.client_settings[client_id]["auto_tts_enabled"] = enabled
            print(f"Client {client_id} auto-TTS: {'enabled' if enabled else 'disabled'}")

    def is_auto_tts_enabled(self, client_id: str) -> bool:
        """Check if auto-TTS is enabled for a specific client."""
        return self.client_settings.get(client_id, {}).get("auto_tts_enabled", True)

    async def broadcast(self, message: str):
        """Broadcast transcription to all clients."""
        if self.active_connections:
            # Send to all connected clients as JSON message
            import json
            message_data = {
                "type": "transcription",
                "text": message
            }
            disconnected = []
            for websocket, client_id in self.active_connections.items():
                try:
                    await websocket.send_text(json.dumps(message_data))
                except Exception as e:
                    print(f"Error sending to client {client_id}: {e}")
                    disconnected.append(websocket)
            
            # Clean up disconnected clients
            for websocket in disconnected:
                self.disconnect(websocket)

    async def broadcast_to_client(self, message, client_id=None):
        """Broadcast message to specific client or all clients."""
        import json
        
        if self.active_connections:
            disconnected = []
            
            if client_id:
                # Send to specific client
                for websocket, cid in self.active_connections.items():
                    if cid == client_id:
                        try:
                            await websocket.send_text(json.dumps(message))
                        except Exception as e:
                            print(f"Error sending to client {client_id}: {e}")
                            disconnected.append(websocket)
                        break
            else:
                # Send to all clients
                for websocket, cid in self.active_connections.items():
                    try:
                        await websocket.send_text(json.dumps(message))
                    except Exception as e:
                        print(f"Error sending to client {cid}: {e}")
                        disconnected.append(websocket)
            
            # Clean up disconnected clients
            for websocket in disconnected:
                self.disconnect(websocket)

    def queue_transcription(self, transcription: str):
        """Thread-safe way to queue transcriptions from STT services"""
        self.transcription_queue.put(transcription)

    def start_tts_playback(self):
        """Signal that TTS playback is starting (for audio ducking)."""
        with self._lock:
            self.tts_active.set()
            print("TTS playback started - STT sensitivity reduced")

    def end_tts_playback(self):
        """Signal that TTS playback has ended (for audio ducking)."""
        with self._lock:
            self.tts_active.clear()
            self.tts_end_time = time.time()
            print(f"TTS playback ended - STT will resume in {self.tts_cooldown_seconds}s")

    def is_stt_suppressed(self):
        """Check if STT should be suppressed due to TTS playback or cooldown."""
        with self._lock:
            # Suppress if TTS is actively playing
            if self.tts_active.is_set():
                return True
            
            # Suppress if we're still in cooldown period after TTS ended
            if self.tts_end_time > 0:
                time_since_tts_end = time.time() - self.tts_end_time
                if time_since_tts_end < self.tts_cooldown_seconds:
                    return True
                else:
                    # Reset the end time after cooldown period
                    self.tts_end_time = 0
            
            return False

    def add_recent_tts_text(self, text: str):
        """Add text to recent TTS list for feedback prevention."""
        with self._lock:
            self.recent_tts_texts.append(text.lower().strip())
            # Keep only the most recent texts
            if len(self.recent_tts_texts) > self.max_recent_tts:
                self.recent_tts_texts.pop(0)

    def is_text_similar_to_recent_tts(self, text: str, similarity_threshold: float = 0.8) -> bool:
        """Check if transcribed text is similar to recently spoken TTS text."""
        if not text.strip():
            return False
            
        text_lower = text.lower().strip()
        
        with self._lock:
            for recent_tts in self.recent_tts_texts:
                # Simple similarity check - could be enhanced with more sophisticated algorithms
                if self._simple_similarity(text_lower, recent_tts) > similarity_threshold:
                    print(f"Filtered potential feedback: '{text}' similar to recent TTS: '{recent_tts}'")
                    return True
        return False

    def _simple_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple similarity between two texts."""
        if not text1 or not text2:
            return 0.0
        
        # Check for exact substring matches
        if text1 in text2 or text2 in text1:
            return 1.0
        
        # Check word overlap
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return 0.0
            
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
