const { pipeline } = require('@xenova/transformers');
const { EventEmitter } = require('events');
const fs = require('fs');
const path = require('path');
const wav = require('wav');
const config = require('../config');

class TranscriptionEngine extends EventEmitter {
  constructor() {
    super();
    this.model = null;
    this.isInitialized = false;
    this.tempDir = path.join(__dirname, '..', 'temp');
    
    // Ensure temp directory exists
    if (!fs.existsSync(this.tempDir)) {
      fs.mkdirSync(this.tempDir, { recursive: true });
    }
  }

  async initialize() {
    if (this.isInitialized) {
      return;
    }

    console.log(`Loading Whisper model: ${config.whisper.model}`);
    
    try {
      // Initialize Whisper model using Transformers.js
      // This automatically downloads the model if not present
      const modelName = this.getModelName(config.whisper.model);
      this.model = await pipeline('automatic-speech-recognition', modelName, {
        quantized: false,
        // Cache models in the models directory
        cache_dir: path.join(__dirname, '..', 'models')
      });
      
      this.isInitialized = true;
      console.log('Whisper model loaded successfully');
      this.emit('initialized');
    } catch (error) {
      console.error('Failed to load Whisper model:', error);
      this.emit('error', error);
      throw error;
    }
  }

  getModelName(modelSize) {
    // Map our config model names to Hugging Face model names
    const modelMap = {
      'tiny': 'Xenova/whisper-tiny',
      'tiny.en': 'Xenova/whisper-tiny.en',
      'base': 'Xenova/whisper-base',
      'base.en': 'Xenova/whisper-base.en',
      'small': 'Xenova/whisper-small',
      'small.en': 'Xenova/whisper-small.en',
      'medium': 'Xenova/whisper-medium',
      'medium.en': 'Xenova/whisper-medium.en',
      'large': 'Xenova/whisper-large-v2',
      'large-v2': 'Xenova/whisper-large-v2',
      'large-v3': 'Xenova/whisper-large-v3'
    };
    
    return modelMap[modelSize] || modelMap['base.en'];
  }

  async transcribe(audioBuffer) {
    if (!this.isInitialized) {
      throw new Error('Transcription engine not initialized');
    }

    try {
      console.log('Transcribing audio...');
      
      // Convert raw audio buffer to the format expected by the model
      const audioData = this.convertAudioBuffer(audioBuffer);
      
      // Transcribe the audio
      const result = await this.model(audioData, {
        language: config.whisper.language,
        task: config.whisper.task,
        return_timestamps: false
      });
      
      if (result && result.text) {
        const text = result.text.trim();
        
        if (text) {
          console.log(`Transcribed: "${text}"`);
          this.emit('transcription', text);
          return text;
        }
      }
      
      return null;
    } catch (error) {
      console.error('Transcription error:', error);
      this.emit('error', error);
      return null;
    }
  }

  convertAudioBuffer(rawAudioBuffer) {
    // Convert 16-bit PCM buffer to Float32Array
    const samples = new Float32Array(rawAudioBuffer.length / 2);
    
    for (let i = 0; i < samples.length; i++) {
      // Read 16-bit signed integer and convert to float (-1 to 1)
      const sample = rawAudioBuffer.readInt16LE(i * 2);
      samples[i] = sample / 32768.0;
    }
    
    return samples;
  }

  cleanup() {
    // Clean up any remaining temporary files
    if (fs.existsSync(this.tempDir)) {
      const files = fs.readdirSync(this.tempDir);
      files.forEach(file => {
        if (file.startsWith('audio_') && file.endsWith('.wav')) {
          fs.unlinkSync(path.join(this.tempDir, file));
        }
      });
    }
  }
}

module.exports = TranscriptionEngine;
