// Configuration for the transcription service
module.exports = {
  // Whisper Model Settings
  whisper: {
    model: 'base.en',        // Model size: tiny, base, small, medium, large
    language: 'en',          // Language code
    task: 'transcribe'       // transcribe or translate
  },

  // Audio Settings
  audio: {
    sampleRate: 16000,       // Sample rate in Hz
    channels: 1,             // Mono audio
    chunkDuration: 1000,     // Chunk duration in ms
    silenceThreshold: 300,   // RMS threshold for silence
    silenceDuration: 2000,   // MS of silence before stopping
    minRecordingDuration: 1000 // Minimum recording length
  },

  // Server Settings
  server: {
    port: 3000,              // HTTP server port
    staticDir: 'public',     // Static files directory
    corsEnabled: true        // Enable CORS for development
  },

  // VAD Configuration
  vad: {
    enableVAD: true,         // Enable voice activity detection
    energyThreshold: 300,    // RMS energy threshold
    silenceFrames: 20        // Number of silent frames before stopping
  }
};
