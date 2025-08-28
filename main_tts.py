#!/usr/bin/env python3
"""
Realtime Speech-to-Text Server with TTS

This is the main entry point for combined STT+TTS operation.
Supports both faster-whisper and Apple Silicon CoreML backends for STT.

Environment Variables:
- STT_SERVICE: 'auto', 'faster-whisper', or 'coreml' (default: 'auto')
- PORT: Server port (default: 8000)

Usage:
    python main_tts.py                    # Auto-detect best STT service
    STT_SERVICE=faster-whisper python main_tts.py  # Force faster-whisper
    STT_SERVICE=coreml python main_tts.py # Force CoreML (Apple Silicon)
"""

import os
import asyncio
import uvicorn
from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from stt.connection_manager import ConnectionManager
from stt.service_factory import create_stt_service
from tts.tts_service import TTSService

# Configuration
PORT = int(os.getenv("PORT", 8000))
STT_SERVICE_TYPE = os.getenv("STT_SERVICE", "auto")

# Initialize FastAPI app
app = FastAPI(title="Realtime Speech-to-Text with TTS")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize connection manager
connection_manager = ConnectionManager()

# Global services
stt_service = None
tts_service = None

@app.on_event("startup")
async def startup_event():
    """Initialize STT and TTS services on startup."""
    global stt_service, tts_service
    
    print(f"Starting STT+TTS server with STT service type: {STT_SERVICE_TYPE}")
    
    try:
        # Initialize STT service (fixed parameter order)
        stt_service = create_stt_service(connection_manager, STT_SERVICE_TYPE)
        print(f"STT service initialized successfully")
        
        # Initialize TTS service
        tts_service = TTSService(connection_manager)
        print(f"TTS service initialized successfully")
        
        # Start the STT service in a background thread
        import threading
        loop = asyncio.get_running_loop()
        thread = threading.Thread(target=stt_service.run, args=(loop,), daemon=True)
        thread.start()
        print("STT service started in background thread")
        
        # Start transcription queue processor
        asyncio.create_task(transcription_queue_processor())
        
    except Exception as e:
        print(f"Failed to initialize services: {e}")
        raise

async def transcription_queue_processor():
    """Background task to process transcription queue and handle auto-TTS."""
    while True:
        try:
            # Process any queued transcriptions
            while not connection_manager.transcription_queue.empty():
                transcription = connection_manager.transcription_queue.get_nowait()
                
                # Broadcast the transcription to all clients (with proper JSON format)
                await connection_manager.broadcast(transcription)
                
                # Handle auto-TTS for clients with it enabled
                if tts_service and transcription.strip():
                    # Check if this transcription is similar to recent TTS output (feedback prevention)
                    if connection_manager.is_text_similar_to_recent_tts(transcription):
                        print(f"Skipping auto-TTS for probable feedback: '{transcription}'")
                        continue
                    
                    # Check if any connected clients have auto-TTS enabled
                    auto_tts_clients = []
                    for client_id in connection_manager.client_settings.keys():
                        if connection_manager.client_settings[client_id].get("auto_tts_enabled", True):  # Default to True
                            auto_tts_clients.append(client_id)
                    
                    if auto_tts_clients:
                        print(f"Auto-TTS: Speaking transcription for {len(auto_tts_clients)} client(s): '{transcription}'")
                        # Process TTS for auto-TTS enabled clients
                        await tts_service.process_tts_request(transcription, auto_tts=True)
                        
        except Exception as e:
            print(f"Error in transcription queue processor: {e}")
        
        await asyncio.sleep(0.1)  # Check queue every 100ms

@app.on_event("shutdown")
async def shutdown_event():
    """Clean shutdown of services."""
    global stt_service, tts_service
    
    print("Shutting down STT+TTS server...")
    
    if stt_service:
        try:
            stt_service.stop()
            print("STT service stopped")
        except Exception as e:
            print(f"Error stopping STT service: {e}")
    
    if tts_service:
        try:
            tts_service.stop()
            print("TTS service stopped")
        except Exception as e:
            print(f"Error stopping TTS service: {e}")

@app.get("/")
async def get_index():
    """Serve the TTS-enabled HTML page."""
    return FileResponse("static/index_tts.html")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time transcription and TTS."""
    client_id = await connection_manager.connect(websocket)
    print(f"Client {client_id} connected")
    
    try:
        while True:
            # Receive data from client
            try:
                message = await websocket.receive_json()
                
                if message.get("type") == "settings":
                    # Handle client settings
                    connection_manager.update_client_settings(client_id, message.get("data", {}))
                    print(f"Updated settings for client {client_id}: {message.get('data', {})}")
                    
                elif message.get("type") == "tts_request":
                    # Handle TTS request (renamed from "tts")
                    text = message.get("text", "")
                    if text and tts_service:
                        await tts_service.process_tts_request(text, client_id, auto_tts=False)
                        
                elif message.get("type") == "auto_tts_toggle":
                    # Handle auto-TTS toggle
                    enabled = message.get("enabled", True)
                    connection_manager.set_auto_tts(client_id, enabled)
                        
            except:
                # If JSON parsing fails, assume it's text data for keep-alive
                data = await websocket.receive_text()
            
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
        "stt_running": stt_service is not None and hasattr(stt_service, 'stop_event') and not stt_service.stop_event.is_set(),
        "tts_running": tts_service is not None and hasattr(tts_service, 'stop_event') and not tts_service.stop_event.is_set()
    }

@app.get("/info")
async def server_info():
    """Get server information."""
    from stt.platform_detector import is_apple_silicon, get_recommended_stt_service
    
    return {
        "server_type": "stt_tts_combined",
        "stt_service": STT_SERVICE_TYPE,
        "platform": "apple_silicon" if is_apple_silicon() else "other",
        "recommended_service": get_recommended_stt_service(),
        "tts_enabled": True,
        "port": PORT
    }

if __name__ == "__main__":
    print(f"Starting Realtime Speech-to-Text Server with TTS")
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
