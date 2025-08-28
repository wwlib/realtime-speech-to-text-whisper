# Audio Feedback Prevention

This document describes the feedback prevention mechanisms implemented to avoid audio loops where TTS output gets picked up by the microphone and re-transcribed.

## Problem

When running the STT+TTS system on a laptop:
1. STT captures microphone input (including laptop speakers)
2. TTS audio is played through laptop speakers 
3. Microphone picks up TTS audio from speakers
4. STT transcribes the TTS audio → creates new TTS → infinite loop

## Solutions Implemented

### 1. Audio Ducking/Suppression

**Primary mechanism**: Temporarily suppress STT processing during TTS playback and cooldown.

- **TTS Active Period**: STT ignores all audio input while TTS is actively streaming
- **Cooldown Period**: STT remains suppressed for 1 second after TTS ends
- **Implementation**: Thread-safe event signaling between TTS and STT services

**Files Modified:**
- `stt/connection_manager.py`: Added TTS state tracking
- `tts/tts_service.py`: Signals TTS start/end events
- `stt/transcription_service.py`: Checks suppression state
- `stt/coreml_transcription_service.py`: Checks suppression state

### 2. Text Similarity Filtering

**Secondary mechanism**: Prevent re-speaking of recently spoken TTS text.

- **Recent Text Tracking**: Maintains list of last 10 TTS outputs
- **Similarity Check**: Compares new transcriptions against recent TTS texts
- **Threshold**: 80% similarity triggers filtering
- **Algorithm**: Word overlap analysis with substring matching

**Benefits:**
- Catches feedback that audio ducking might miss
- Prevents repetitive loops even with timing gaps
- Configurable similarity threshold

### 3. Implementation Details

#### Audio Ducking Flow:
```
TTS Request → TTS Start Signal → STT Suppressed → Audio Streaming → 
TTS End Signal → Cooldown Period → STT Resumes
```

#### Text Filtering Flow:
```
Transcription → Similarity Check → Filter if Similar → Process if Different
```

## Configuration

### Timing Parameters (in `connection_manager.py`):
```python
self.tts_cooldown_seconds = 1.0  # Cooldown after TTS ends
```

### Text Filtering Parameters (in `connection_manager.py`):
```python
self.max_recent_tts = 10  # Number of recent TTS texts to track
similarity_threshold = 0.8  # 80% similarity threshold
```

## Testing

To test feedback prevention:

1. Start the TTS server: `python main_tts.py`
2. Enable auto-TTS in the web interface
3. Speak a phrase
4. Observe that the TTS output doesn't get re-transcribed
5. Check console logs for suppression messages

**Expected Console Output:**
```
TTS playback started - STT sensitivity reduced
Auto-TTS: Speaking transcription for 1 client(s): 'hello world'
Estimated playback duration: 1.23s
TTS playback ended - STT will resume in 1s
```

## Hardware Solutions (Alternative)

For production deployments, consider these hardware approaches:

### 1. Headphones/Earbuds
- **Simplest solution**: Use headphones for TTS output
- **Pros**: 100% effective, no code changes needed
- **Cons**: Requires user to wear headphones

### 2. Acoustic Echo Cancellation (AEC)
- **Libraries**: WebRTC, Speex, OpenAL Soft
- **Implementation**: Real-time audio processing
- **Complexity**: Requires audio pipeline integration

### 3. Directional Microphones
- **Hardware**: Beam-forming or shotgun microphones
- **Benefit**: Reduced speaker pickup
- **Cost**: Higher hardware cost

### 4. Separate Audio Devices
- **Setup**: USB microphone + separate speakers/headphones
- **Benefit**: Physical audio isolation
- **Implementation**: Device-specific audio routing

## Advanced Solutions

### 1. Voice Activity Detection (VAD) Enhancement
- Use ML-based VAD to distinguish human vs synthetic speech
- Requires training data and additional processing

### 2. Speaker Recognition
- Train model to recognize and filter out the TTS voice
- Complex but highly effective

### 3. Real-time Audio Processing
- Implement echo cancellation in the audio pipeline
- Most complex but most professional solution

## Performance Impact

The implemented solutions have minimal performance impact:

- **Audio Ducking**: Negligible (simple event checking)
- **Text Filtering**: ~1ms per transcription (string operations)
- **Memory Usage**: <1KB (stores ~10 recent text strings)

## Troubleshooting

### If feedback still occurs:

1. **Increase cooldown period**: Modify `tts_cooldown_seconds`
2. **Lower similarity threshold**: Reduce from 0.8 to 0.6
3. **Check timing**: Ensure TTS signals are working (check console logs)
4. **Volume levels**: Reduce speaker volume relative to microphone sensitivity

### Debug logging:
- TTS start/end events are logged to console
- Filtered transcriptions are logged with reasons
- STT suppression state can be monitored

## Future Enhancements

1. **Adaptive thresholds**: Adjust based on ambient noise levels
2. **ML-based filtering**: Use neural networks for better speech distinction
3. **User controls**: Web interface controls for tuning parameters
4. **Audio analysis**: Real-time frequency analysis for better filtering
