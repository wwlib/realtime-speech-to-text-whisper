const express = require('express');
const http = require('http');
const path = require('path');
const TranscriptionService = require('./src/transcriptionService');
const config = require('./config');

const app = express();
const server = http.createServer(app);

// Serve static files
app.use(express.static(path.join(__dirname, config.server.staticDir)));

// Create transcription service
const transcriptionService = new TranscriptionService();

// Initialize WebSocket
transcriptionService.initializeWebSocket(server);

// Routes
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, config.server.staticDir, 'index.html'));
});

app.get('/health', (req, res) => {
    res.json({
        status: 'ok',
        service: transcriptionService.isRunning ? 'running' : 'stopped',
        timestamp: new Date().toISOString()
    });
});

// Graceful shutdown handler
function gracefulShutdown() {
    console.log('\nReceived shutdown signal. Cleaning up...');
    
    transcriptionService.cleanup();
    
    server.close(() => {
        console.log('Server closed. Exiting...');
        process.exit(0);
    });
    
    // Force exit after 10 seconds
    setTimeout(() => {
        console.log('Force exiting...');
        process.exit(1);
    }, 10000);
}

// Handle shutdown signals
process.on('SIGINT', gracefulShutdown);
process.on('SIGTERM', gracefulShutdown);

// Initialize and start server
async function startServer() {
    try {
        console.log('Initializing transcription service...');
        const initialized = await transcriptionService.initialize();
        
        if (!initialized) {
            console.error('Failed to initialize transcription service');
            process.exit(1);
        }

        server.listen(config.server.port, () => {
            console.log(`\n🚀 Transcription Service Started`);
            console.log(`📡 Server: http://localhost:${config.server.port}`);
            console.log(`🎤 Model: ${config.whisper.model}`);
            console.log(`🔊 Sample Rate: ${config.audio.sampleRate}Hz`);
            console.log(`🎯 VAD Enabled: ${config.vad.enableVAD}`);
            console.log('\nPress Ctrl+C to stop the service\n');
            
            // Auto-start transcription service
            setTimeout(() => {
                transcriptionService.start();
            }, 1000);
        });

    } catch (error) {
        console.error('Failed to start server:', error);
        process.exit(1);
    }
}

startServer();
