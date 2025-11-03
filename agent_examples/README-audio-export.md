# Transcript Narrator - Audio Export Guide

## 24-bit PCM at 16kHz Output

The transcript narrator now exports audio as **24-bit PCM at 16kHz** by default.

### Audio Specifications

- **Bit Depth**: 24-bit PCM (high quality)
- **Sample Rate**: 16,000 Hz (optimal for speech)
- **Channels**: Mono
- **Format**: WAV

### Requirements

**Required:**
- `numpy`
- `piper-tts`

**Optional (for sample rate conversion):**
- `scipy` - Enables resampling from Piper's native 22.05kHz to 16kHz

If scipy is not installed, the audio will use the native sample rate from the TTS engine (typically 22.05kHz).

### Installing scipy (Optional)

```bash
pip install scipy
```

### Usage

Export transcript to 24-bit PCM audio:

```bash
python agent_examples/transcript_narrator_example.py
```

Choose mode 3 or 4 to export audio files.

### Audio Quality Comparison

**16-bit vs 24-bit:**
- 16-bit: Dynamic range of ~96 dB
- 24-bit: Dynamic range of ~144 dB (much better for post-processing)

**Sample Rates:**
- 16 kHz: Standard for speech applications, smaller files
- 22.05 kHz: Piper's native rate (used if scipy not available)
- 44.1 kHz: CD quality (overkill for TTS)

### File Sizes

Approximate file sizes for 1 minute of audio:
- 16-bit @ 16kHz: ~1.9 MB
- 24-bit @ 16kHz: ~2.8 MB
- 16-bit @ 22.05kHz: ~2.6 MB

### Example Output

```
Exporting transcript to audio file...
Format: 24-bit PCM, 16000 Hz, Mono
Default pause: 0.5s between turns
============================================================
[Turn 0] Clinician: "Hello. I am Dr. Smith..."
  Resampled from 22050 Hz to 16000 Hz
[Turn 1] Patient: "Hi, Dr. Smith. I'm feeling okay..."
============================================================
✓ Audio file saved: narration.wav
  Format: 24-bit PCM, 16000 Hz, Mono
  Duration: 45.2 seconds
  File size: 2123.4 KB
============================================================
```

### Custom Pauses

You can control pauses between turns in three ways:

1. **Global pause** (interactive prompt):
   ```
   Pause between turns in seconds (default: 0.5): 1.5
   ```

2. **Per-turn pause** (in JSON):
   ```json
   {
     "index": 1,
     "speaker": "Patient",
     "text": "...",
     "pause_after": 2.0
   }
   ```

3. **No pause**:
   ```
   Pause between turns in seconds (default: 0.5): 0
   ```

### Technical Notes

**24-bit PCM Encoding:**
- Values are scaled to range: -8,388,607 to +8,388,607
- Stored as 3 bytes per sample (little-endian)
- Compatible with all major audio software (Audacity, Adobe Audition, etc.)

**Resampling:**
- Uses scipy.signal.resample for high-quality conversion
- Preserves audio quality during sample rate conversion
- Falls back to native rate if scipy unavailable

### Troubleshooting

**No scipy warning:**
```
Warning: scipy not installed, keeping original sample rate 22050 Hz
```
Solution: Install scipy with `pip install scipy`

**Playback issues:**
If playback doesn't work with afplay, the exported file is still valid. Use any audio player:
```bash
# macOS
open narration.wav

# Or specify player
vlc narration.wav
```


### Sample Execution

```bash
python agent_examples/transcript_narrator_example.py
============================================================
Transcript Narrator with Multi-Voice TTS
============================================================

Default transcript: /Users/andrewrapo/github/wwlib/realtime-speech-to-text-whisper/agent_examples/transcript-1.json
Enter transcript path (or press Enter for default): agent_examples/large-transcript-example-1.json
✓ Loaded transcript: large-transcript-example-1.json
  28 turns found
Found voice: en_US-amy-medium
Found voice: en_US-lessac-medium
Found voice: en_US-ryan-high

✓ Available voices: ['en_US-amy-medium', 'en_US-lessac-medium', 'en_US-ryan-high']

Speakers in transcript: {'Clinician'}

Voice assignments:
  Clinician → en_US-amy-medium

Loading voices...
Loaded voice: en_US-amy-medium

Narration modes:
1. Auto-play entire transcript
2. Interactive mode (step through turns)
3. Export to audio file (no playback)
4. Export to audio file AND play
Choose mode (1-4): 3
Pause between turns in seconds (default: 0.5): 2
Using pause duration: 2.0s

Output filename (default: narration.wav): long-transcript-2.wav

============================================================
Exporting transcript to audio file...
Format: 24-bit PCM, 16000 Hz, Mono
Default pause: 2.0s between turns
============================================================
[Turn 0] Clinician: "Alright, um, so we've got a 68-year-old patient he..."
[Turn 1] Clinician: (empty - skipped)
[Turn 2] Clinician: "Now, uh, the patient, um, is on, uh, moderate bed ..."
[Turn 3] Clinician: (empty - skipped)
[Turn 4] Clinician: "Respiratory-wise, um, the patient has a, uh, produ..."
[Turn 5] Clinician: (empty - skipped)
[Turn 6] Clinician: "Uh, blood pressure's being monitored on the, uh, r..."
[Turn 7] Clinician: (empty - skipped)
[Turn 8] Clinician: "Uh, urine output has been, uh, less than 150 mL pe..."
[Turn 9] Clinician: "Alright, let's see... we've got an elderly female ..."
[Turn 10] Clinician: (empty - skipped)
[Turn 11] Clinician: "Her heart rate is stable at 72 beats per minute, a..."
[Turn 12] Clinician: (empty - skipped)
[Turn 13] Clinician: "She reported nausea but hasn't vomited, although t..."
[Turn 14] Clinician: (empty - skipped)
[Turn 15] Clinician: "Her mobility is slightly limited, which is somethi..."
[Turn 16] Clinician: (empty - skipped)
[Turn 17] Clinician: "Overall, her vital signs and fluid management are ..."
[Turn 18] Clinician: "Alright, let's see here. We have a 68-year-old fem..."
[Turn 19] Clinician: (empty - skipped)
[Turn 20] Clinician: "I'm seeing labored breathing, and there's definite..."
[Turn 21] Clinician: (empty - skipped)
[Turn 22] Clinician: "Uh, the patient also has a prescription for, uh, a..."
[Turn 23] Clinician: (empty - skipped)
[Turn 24] Clinician: "Uh, her heart rate is, uh, 110 bpm, and, uh, she's..."
[Turn 25] Clinician: (empty - skipped)
[Turn 26] Clinician: "Okay, I think that covers the, uh, main points...."
[Turn 27] Clinician: "The forth patient is, uh, slightly limited in mobi..."
  Resampled from 22050 Hz to 16000 Hz

============================================================
✓ Audio file saved: long-transcript-2.wav
  Format: 24-bit PCM, 16000 Hz, Mono
  Duration: 382.5 seconds
  File size: 17930.4 KB
============================================================
```