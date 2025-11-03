const mic = require('mic');
const { EventEmitter } = require('events');
const config = require('../config');

class AudioCapture extends EventEmitter {
  constructor() {
    super();
    this.micInstance = null;
    this.micInputStream = null;
    this.isRecording = false;
    this.audioBuffer = [];
    this.silentFrames = 0;
    this.recordingStartTime = null;
  }

  start() {
    if (this.isRecording) {
      console.log('Already recording');
      return;
    }

    console.log('Starting audio capture...');
    
    // Configure microphone
    this.micInstance = mic({
      rate: config.audio.sampleRate,
      channels: config.audio.channels,
      debug: false,
      exitOnSilence: 0,
      fileType: 'raw',
      encoding: 'signed-integer',
      bitwidth: 16,
      endian: 'little'
    });

    this.micInputStream = this.micInstance.getAudioStream();
    this.isRecording = true;
    this.audioBuffer = [];
    this.silentFrames = 0;

    this.micInputStream.on('data', (chunk) => {
      this.processAudioChunk(chunk);
    });

    this.micInputStream.on('error', (err) => {
      console.error('Microphone error:', err);
      this.emit('error', err);
    });

    this.micInputStream.on('startComplete', () => {
      console.log('Microphone started successfully');
      this.emit('started');
    });

    this.micInputStream.on('stopComplete', () => {
      console.log('Microphone stopped');
      this.emit('stopped');
    });

    this.micInputStream.on('processExitComplete', () => {
      console.log('Microphone process exited');
    });

    // Start the microphone
    this.micInstance.start();
  }

  stop() {
    if (!this.isRecording) {
      return;
    }

    console.log('Stopping audio capture...');
    this.isRecording = false;
    
    if (this.micInstance) {
      this.micInstance.stop();
      this.micInstance = null;
      this.micInputStream = null;
    }

    this.emit('stopped');
  }

  processAudioChunk(chunk) {
    if (!this.isRecording) return;

    // Calculate RMS energy for voice activity detection
    const energy = this.calculateRMS(chunk);
    
    if (config.vad.enableVAD) {
      if (energy > config.vad.energyThreshold) {
        // Voice detected
        this.silentFrames = 0;
        
        if (this.audioBuffer.length === 0) {
          // Start of new recording
          this.recordingStartTime = Date.now();
          console.log('Voice activity detected, starting recording...');
          this.emit('recordingStarted');
        }
        
        this.audioBuffer.push(chunk);
      } else {
        // Silence detected
        this.silentFrames++;
        
        if (this.audioBuffer.length > 0) {
          // We're in the middle of a recording
          this.audioBuffer.push(chunk);
          
          // Check if we've had enough silence to stop recording
          if (this.silentFrames >= config.vad.silenceFrames) {
            this.finishRecording();
          }
        }
      }
    } else {
      // No VAD, just accumulate all audio
      this.audioBuffer.push(chunk);
    }
  }

  finishRecording() {
    if (this.audioBuffer.length === 0) return;

    const recordingDuration = Date.now() - this.recordingStartTime;
    
    // Check minimum recording duration
    if (recordingDuration < config.audio.minRecordingDuration) {
      console.log(`Recording too short (${recordingDuration}ms), ignoring...`);
      this.audioBuffer = [];
      this.silentFrames = 0;
      return;
    }

    console.log(`Recording finished: ${recordingDuration}ms, ${this.audioBuffer.length} chunks`);
    
    // Combine all audio chunks
    const totalLength = this.audioBuffer.reduce((sum, chunk) => sum + chunk.length, 0);
    const combinedAudio = Buffer.concat(this.audioBuffer, totalLength);
    
    // Emit the complete recording
    this.emit('audioReady', combinedAudio);
    
    // Reset for next recording
    this.audioBuffer = [];
    this.silentFrames = 0;
    this.recordingStartTime = null;
  }

  calculateRMS(buffer) {
    let sum = 0;
    const samples = buffer.length / 2; // 16-bit samples
    
    for (let i = 0; i < buffer.length; i += 2) {
      // Convert to 16-bit signed integer
      const sample = buffer.readInt16LE(i);
      sum += sample * sample;
    }
    
    return Math.sqrt(sum / samples);
  }
}

module.exports = AudioCapture;
