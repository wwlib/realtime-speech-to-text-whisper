#!/usr/bin/env python3
"""
Realtime Speech-to-Text Server (STT Only)

This is the main entry point for STT-only operation.
Supports both faster-whisper and Apple Silicon CoreML backends.

Environment Variables:
- STT_SERVICE: 'auto', 'faster-whisper', or 'coreml' (default: 'auto')
- PORT: Server port (default: 8000)

Usage:
    python main.py                    # Auto-detect best STT service
    STT_SERVICE=faster-whisper python main.py  # Force faster-whisper
    STT_SERVICE=coreml python main.py # Force CoreML (Apple Silicon)
"""

import os
import asyncio
import uvicorn
from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from stt.connection_manager import ConnectionManager
from stt.service_factory import create_stt_service

# Configuration
PORT = int(os.getenv("PORT", 8000))
STT_SERVICE_TYPE = os.getenv("STT_SERVICE", "auto")

# Initialize FastAPI app
app = FastAPI(title="Realtime Speech-to-Text Server")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize connection manager
connection_manager = ConnectionManager()

# Global STT service
stt_service = None

@app.on_event("startup")
async def startup_event():
    """Initialize STT service on startup."""
    global stt_service
    
    print(f"Starting STT server with service type: {STT_SERVICE_TYPE}")
    
    try:
        stt_service = create_stt_service(connection_manager, STT_SERVICE_TYPE)
        print(f"STT service initialized successfully")
        
        # Start the STT service in a background thread
        import threading
        loop = asyncio.get_running_loop()
        thread = threading.Thread(target=stt_service.run, args=(loop,), daemon=True)
        thread.start()
        print("STT service started in background thread")
        
        # Start transcription queue processor
        asyncio.create_task(transcription_queue_processor())
        
    except Exception as e:
        print(f"Failed to initialize STT service: {e}")
        raise

async def transcription_queue_processor():
    """Background task to process transcription queue."""
    while True:
        await connection_manager.process_transcription_queue()
        await asyncio.sleep(0.1)  # Check queue every 100ms

@app.on_event("shutdown")
async def shutdown_event():
    """Clean shutdown of services."""
    global stt_service
    
    print("Shutting down STT server...")
    
    if stt_service:
        try:
            stt_service.stop()
            print("STT service stopped")
        except Exception as e:
            print(f"Error stopping STT service: {e}")

@app.get("/")
async def get_index():
    """Serve the main HTML page."""
    return FileResponse("static/index.html")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time transcription."""
    client_id = await connection_manager.connect(websocket)
    print(f"Client {client_id} connected")
    
    try:
        while True:
            # Keep the connection alive - STT service captures audio directly from microphone
            await websocket.receive_text()
            
    except Exception as e:
        print(f"WebSocket error for client {client_id}: {e}")
    finally:
        connection_manager.disconnect(websocket)
        print(f"Client {client_id} disconnected")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "stt_service": STT_SERVICE_TYPE,
        "stt_running": stt_service is not None and hasattr(stt_service, 'stop_event') and not stt_service.stop_event.is_set()
    }

@app.get("/info")
async def server_info():
    """Get server information."""
    from stt.platform_detector import is_apple_silicon, get_recommended_stt_service
    
    return {
        "server_type": "stt_only",
        "stt_service": STT_SERVICE_TYPE,
        "platform": "apple_silicon" if is_apple_silicon() else "other",
        "recommended_service": get_recommended_stt_service(),
        "port": PORT
    }

if __name__ == "__main__":
    print(f"Starting Realtime Speech-to-Text Server (STT Only)")
    print(f"STT Service: {STT_SERVICE_TYPE}")
    print(f"Port: {PORT}")
    print(f"WebSocket endpoint: ws://localhost:{PORT}/ws")
    print(f"Web interface: http://localhost:{PORT}")
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=PORT,
        log_level="info"
    )
