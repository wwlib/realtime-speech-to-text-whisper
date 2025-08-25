import asyncio
import threading
import signal
import sys
import queue
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn

from transcription_service import TranscriptionService
from tts_service import TTSService

# Global queue for transcriptions
transcription_queue = queue.Queue()

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[WebSocket, str] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[websocket] = client_id
        print(f"Client {client_id} connected")

    def disconnect(self, websocket: WebSocket):
        client_id = self.active_connections.pop(websocket, "unknown")
        print(f"Client {client_id} disconnected")

    async def broadcast(self, message: str):
        """Broadcast transcription to all clients."""
        print(f"Broadcasting transcription to {len(self.active_connections)} clients: '{message}'")
        if self.active_connections:
            message_data = {"type": "transcription", "text": message}
            await self._send_to_all(message_data)
        else:
            print("No active connections to broadcast to")

    def queue_transcription(self, message: str):
        """Queue a transcription to be broadcast (thread-safe)."""
        transcription_queue.put(message)

    async def broadcast_to_client(self, message: dict, client_id: str = None):
        """Send message to specific client or all clients."""
        if client_id:
            # Send to specific client
            for websocket, cid in self.active_connections.items():
                if cid == client_id:
                    try:
                        await websocket.send_json(message)
                    except Exception as e:
                        print(f"Error sending to client {client_id}: {e}")
                    break
        else:
            # Send to all clients
            await self._send_to_all(message)

    async def _send_to_all(self, message: dict):
        """Send message to all connected clients."""
        disconnected = []
        print(f"Sending message to {len(self.active_connections)} clients: {message}")
        for websocket in self.active_connections:
            try:
                await websocket.send_json(message)
                print(f"Message sent successfully to client")
            except Exception as e:
                print(f"Error broadcasting: {e}")
                disconnected.append(websocket)
        
        # Clean up disconnected clients
        for websocket in disconnected:
            self.disconnect(websocket)

app = FastAPI()
manager = ConnectionManager()
transcription_service = None
tts_service = None

async def process_transcription_queue():
    """Background task to process transcriptions from the queue."""
    while True:
        try:
            # Check for transcriptions with a short timeout
            transcription = transcription_queue.get(timeout=0.1)
            await manager.broadcast(transcription)
        except queue.Empty:
            pass
        except Exception as e:
            print(f"Error processing transcription queue: {e}")
        
        # Small delay to prevent busy waiting
        await asyncio.sleep(0.1)

# Start the background task
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(process_transcription_queue())

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def get():
    return HTMLResponse(open("static/index_tts.html").read())

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_json()
            
            # Handle TTS requests
            if data.get("type") == "tts_request":
                text = data.get("text", "")
                if text and tts_service:
                    # Process TTS request for this specific client
                    await tts_service.process_tts_request(text, client_id)
                    
    except WebSocketDisconnect:
        manager.disconnect(websocket)

def signal_handler(signum, frame):
    print("\nReceived interrupt signal. Shutting down gracefully...")
    if transcription_service:
        transcription_service.stop()
    if tts_service:
        tts_service.stop()
    sys.exit(0)

if __name__ == "__main__":
    # Set up signal handling
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("Starting Realtime Speech-to-Text with TTS Server...")
    
    # Create services
    transcription_service = TranscriptionService(manager)
    tts_service = TTSService(manager)
    
    # Start transcription service in a separate thread
    loop = asyncio.new_event_loop()
    transcription_thread = threading.Thread(
        target=transcription_service.run,
        args=(loop,),
        daemon=True
    )
    transcription_thread.start()
    
    # Start the FastAPI server
    try:
        uvicorn.run(app, host="0.0.0.0", port=8001)
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)
