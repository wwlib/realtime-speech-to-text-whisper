const WebSocket = require('ws');
const { EventEmitter } = require('events');

class WebSocketManager extends EventEmitter {
  constructor() {
    super();
    this.wss = null;
    this.clients = new Set();
  }

  initialize(server) {
    this.wss = new WebSocket.Server({ server });
    
    this.wss.on('connection', (ws, req) => {
      console.log(`New WebSocket connection from ${req.socket.remoteAddress}`);
      this.clients.add(ws);
      
      // Send welcome message
      ws.send(JSON.stringify({
        type: 'status',
        message: 'Connected to transcription service'
      }));

      ws.on('message', (message) => {
        try {
          const data = JSON.parse(message);
          this.emit('message', data, ws);
        } catch (error) {
          console.error('Invalid WebSocket message:', error);
        }
      });

      ws.on('close', () => {
        console.log('WebSocket connection closed');
        this.clients.delete(ws);
      });

      ws.on('error', (error) => {
        console.error('WebSocket error:', error);
        this.clients.delete(ws);
      });
    });

    console.log('WebSocket server initialized');
    this.emit('initialized');
  }

  broadcast(message) {
    const data = typeof message === 'string' ? message : JSON.stringify(message);
    
    this.clients.forEach(client => {
      if (client.readyState === WebSocket.OPEN) {
        client.send(data);
      }
    });
  }

  broadcastTranscription(text) {
    this.broadcast(JSON.stringify({
      type: 'transcription',
      text: text,
      timestamp: new Date().toISOString()
    }));
  }

  broadcastStatus(status, message) {
    this.broadcast(JSON.stringify({
      type: 'status',
      status: status,
      message: message,
      timestamp: new Date().toISOString()
    }));
  }

  getClientCount() {
    return this.clients.size;
  }

  close() {
    if (this.wss) {
      this.clients.forEach(client => {
        client.close();
      });
      this.wss.close();
    }
  }
}

module.exports = WebSocketManager;
