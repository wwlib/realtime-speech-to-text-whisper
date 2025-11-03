const AudioCapture = require('./audioCapture');
const TranscriptionEngine = require('./transcriptionEngine');
const WebSocketManager = require('./webSocketManager');
const config = require('../config');

class TranscriptionService {
  constructor() {
    this.audioCapture = new AudioCapture();
    this.transcriptionEngine = new TranscriptionEngine();
    this.webSocketManager = new WebSocketManager();
    this.isRunning = false;
    
    this.setupEventHandlers();
  }

  setupEventHandlers() {
    // Audio capture events
    this.audioCapture.on('started', () => {
      console.log('Audio capture started');
      this.webSocketManager.broadcastStatus('listening', 'Listening for speech...');
    });

    this.audioCapture.on('recordingStarted', () => {
      console.log('Recording started');
      this.webSocketManager.broadcastStatus('recording', 'Recording speech...');
    });

    this.audioCapture.on('audioReady', async (audioBuffer) => {
      console.log('Audio ready for transcription');
      this.webSocketManager.broadcastStatus('transcribing', 'Transcribing audio...');
      
      try {
        const transcription = await this.transcriptionEngine.transcribe(audioBuffer);
        if (transcription) {
          this.webSocketManager.broadcastTranscription(transcription);
        }
      } catch (error) {
        console.error('Transcription failed:', error);
        this.webSocketManager.broadcastStatus('error', 'Transcription failed');
      }
      
      // Return to listening state
      this.webSocketManager.broadcastStatus('listening', 'Listening for speech...');
    });

    this.audioCapture.on('stopped', () => {
      console.log('Audio capture stopped');
      this.webSocketManager.broadcastStatus('stopped', 'Audio capture stopped');
    });

    this.audioCapture.on('error', (error) => {
      console.error('Audio capture error:', error);
      this.webSocketManager.broadcastStatus('error', 'Audio capture error');
    });

    // Transcription engine events
    this.transcriptionEngine.on('initialized', () => {
      console.log('Transcription engine initialized');
    });

    this.transcriptionEngine.on('transcription', (text) => {
      console.log(`Transcription received: ${text}`);
    });

    this.transcriptionEngine.on('error', (error) => {
      console.error('Transcription engine error:', error);
    });

    // WebSocket events
    this.webSocketManager.on('initialized', () => {
      console.log('WebSocket manager initialized');
    });

    this.webSocketManager.on('message', (data, ws) => {
      this.handleWebSocketMessage(data, ws);
    });
  }

  handleWebSocketMessage(data, ws) {
    switch (data.type) {
      case 'start':
        this.start();
        break;
      case 'stop':
        this.stop();
        break;
      case 'status':
        ws.send(JSON.stringify({
          type: 'status',
          status: this.isRunning ? 'running' : 'stopped',
          clients: this.webSocketManager.getClientCount()
        }));
        break;
      default:
        console.log('Unknown WebSocket message type:', data.type);
    }
  }

  async initialize() {
    console.log('Initializing transcription service...');
    
    try {
      await this.transcriptionEngine.initialize();
      console.log('Transcription service initialized successfully');
      return true;
    } catch (error) {
      console.error('Failed to initialize transcription service:', error);
      return false;
    }
  }

  initializeWebSocket(server) {
    this.webSocketManager.initialize(server);
  }

  async start() {
    if (this.isRunning) {
      console.log('Transcription service already running');
      return;
    }

    console.log('Starting transcription service...');
    this.isRunning = true;
    
    try {
      this.audioCapture.start();
      console.log('Transcription service started successfully');
    } catch (error) {
      console.error('Failed to start transcription service:', error);
      this.isRunning = false;
      throw error;
    }
  }

  stop() {
    if (!this.isRunning) {
      console.log('Transcription service not running');
      return;
    }

    console.log('Stopping transcription service...');
    this.isRunning = false;
    
    this.audioCapture.stop();
    console.log('Transcription service stopped');
  }

  cleanup() {
    this.stop();
    this.transcriptionEngine.cleanup();
    this.webSocketManager.close();
  }
}

module.exports = TranscriptionService;
