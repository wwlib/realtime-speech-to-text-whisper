from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from typing import List
import asyncio
import threading

# Import the CoreML transcription service
from coreml_transcription_service import CoreMLTranscriptionService

app = FastAPI()

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()
transcription_service = CoreMLTranscriptionService(manager)

@app.on_event("startup")
async def startup_event():
    """Start the CoreML transcription service in a background thread."""
    print("Starting CoreML transcription service...")
    loop = asyncio.get_running_loop()
    thread = threading.Thread(target=transcription_service.run, args=(loop,), daemon=True)
    thread.start()
    print("CoreML transcription service started.")

@app.on_event("shutdown")
async def shutdown_event():
    """Stop the transcription service gracefully."""
    print("Shutting down CoreML transcription service...")
    transcription_service.stop()
    print("CoreML transcription service shutdown complete.")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    print(f"New client connected. Total clients: {len(manager.active_connections)}")
    try:
        while True:
            # Keep the connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print(f"Client disconnected. Total clients: {len(manager.active_connections)}")

# Mount the static directory to serve the frontend
app.mount("/", StaticFiles(directory="static", html=True), name="static")
