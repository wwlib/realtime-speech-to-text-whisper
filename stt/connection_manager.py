import queue
from fastapi import WebSocket


class ConnectionManager:
    """Manages WebSocket connections and transcription queue for thread-safe communication"""
    
    def __init__(self):
        self.active_connections: dict[WebSocket, str] = {}
        self.client_settings: dict[str, dict] = {}  # Track client settings including auto-TTS
        self.transcription_queue = queue.Queue()  # For thread-safe communication between STT and main

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
