# Transcript Narrator - Audio Export Guide

## Multiple Audio Format Options

The transcript narrator supports **three audio output formats** to meet different needs.

### Supported Formats

1. **16-bit PCM @ 22050 Hz** (Original)
   - Linear PCM, 16-bit little-endian signed integer
   - 22,050 Hz sample rate (Piper's native rate)
   - No resampling required
   - Smallest file size

2. **16-bit PCM @ 16000 Hz**
   - Linear PCM, 16-bit little-endian signed integer
   - 16,000 Hz sample rate (standard for speech)
   - Resampled from 22050 Hz (requires scipy)
   - Good balance of quality and size

3. **24-bit PCM @ 16000 Hz** (Default)
   - Linear PCM, 24-bit little-endian signed integer
   - 16,000 Hz sample rate (standard for speech)
   - Resampled from 22050 Hz (requires scipy)
   - Highest quality, best for post-processing

### Requirements

**Required:**
- `numpy`
- `piper-tts`

**Optional (for sample rate conversion):**
- `scipy` - Enables resampling from 22.05kHz to 16kHz
- Without scipy: 16kHz formats will fall back to 22.05kHz

### Installing scipy (Recommended)

```bash
pip install scipy
```

### Usage

Run the narrator and choose your format:

```bash
python agent_examples/transcript_narrator_example.py
```

When you select mode 3 or 4 (Export), you'll be prompted:

```
Audio format options:
1. 16-bit PCM, 22050 Hz (Original)
2. 16-bit PCM, 16000 Hz
3. 24-bit PCM, 16000 Hz (Default)
Choose format (1-3, default: 3):
```

### Smart Default Filenames

The app automatically generates descriptive filenames based on your input transcript and chosen options:

**Format:** `{transcript-name}_{format}_{pause}.wav`

**Examples:**
- Input: `transcript-1.json`, 24-bit/16kHz, 0.5s pause
  - Output: `transcript-1_24bit-16000hz_pause0p5s.wav`

- Input: `large-transcript-example-1.json`, 16-bit/16kHz, 2.0s pause
  - Output: `large-transcript-example-1_16bit-16000hz_pause2s.wav`

- Input: `nurse-interview.json`, 16-bit/22050Hz, 1.5s pause
  - Output: `nurse-interview_16bit-22050hz_pause1p5s.wav`

You can still provide a custom filename when prompted, or just press Enter to use the smart default!

### Audio Quality Comparison

**Bit Depth:**
- 16-bit: Dynamic range of ~96 dB (standard quality)
- 24-bit: Dynamic range of ~144 dB (professional quality, better for editing)

**Sample Rates:**
- 22,050 Hz: Piper's native rate, no quality loss
- 16,000 Hz: Industry standard for speech applications
- Both are excellent for voice/speech content

### File Size Comparison

For 1 minute of audio:
- 16-bit @ 22.05 kHz: ~2.6 MB (smallest)
- 16-bit @ 16.0 kHz: ~1.9 MB
- 24-bit @ 16.0 kHz: ~2.8 MB (largest)

### When to Use Each Format

**16-bit @ 22050 Hz:**
- ✅ Maximum compatibility
- ✅ No resampling artifacts
- ✅ Fastest processing
- ✅ Use when you need Piper's exact output

**16-bit @ 16000 Hz:**
- ✅ Standard speech format
- ✅ Smaller file sizes
- ✅ Compatible with most speech AI systems
- ✅ Use for speech recognition, telephony, voice apps

**24-bit @ 16000 Hz:**
- ✅ Professional audio quality
- ✅ Best for post-processing (EQ, compression, effects)
- ✅ Maximum dynamic range
- ✅ Use for production, editing, archival

### File Sizes

Approximate file sizes for 1 minute of audio:
- 16-bit @ 16kHz: ~1.9 MB
- 24-bit @ 16kHz: ~2.8 MB
- 16-bit @ 22.05kHz: ~2.6 MB

### Example Output

```
Narration modes:
1. Auto-play entire transcript
2. Interactive mode (step through turns)
3. Export to audio file (no playback)
4. Export to audio file AND play
Choose mode (1-4): 3

Audio format options:
1. 16-bit PCM, 22050 Hz (Original)
2. 16-bit PCM, 16000 Hz
3. 24-bit PCM, 16000 Hz (Default)
Choose format (1-3, default: 3): 2
Selected: 16-bit PCM, 16000 Hz

Pause between turns in seconds (default: 0.5): 1.0
Using pause duration: 1.0s

Output filename (default: transcript-1_16bit-16000hz_pause1s.wav): 

============================================================
Exporting transcript to audio file...
Format: 16-bit PCM, 16000 Hz, Mono
Default pause: 1.0s between turns
============================================================
[Turn 0] Clinician: "Hello. I am Dr. Smith..."
  Resampled from 22050 Hz to 16000 Hz
[Turn 1] Patient: "Hi, Dr. Smith. I'm feeling okay..."
============================================================
✓ Audio file saved: transcript-1_16bit-16000hz_pause1s.wav
  Format: 16-bit PCM, 16000 Hz, Mono
  Duration: 45.2 seconds
  File size: 1416.3 KB
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

**16-bit PCM Encoding:**
- Values are scaled to range: -32,767 to +32,767
- Stored as 2 bytes per sample (little-endian)
- Standard CD quality format

**24-bit PCM Encoding:**
- Values are scaled to range: -8,388,607 to +8,388,607
- Stored as 3 bytes per sample (little-endian)
- Professional audio format
- Compatible with all major audio software (Audacity, Adobe Audition, Pro Tools, etc.)

**Resampling:**
- Uses `scipy.signal.resample` for high-quality conversion
- Preserves audio quality during sample rate conversion
- Falls back to native rate (22050 Hz) if scipy unavailable

**All formats:**
- Mono channel (1 channel)
- Little-endian byte order
- WAV container format
- Standard PCM encoding (no compression)

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

Audio format options:
1. 16-bit PCM, 22050 Hz (Original)
2. 16-bit PCM, 16000 Hz
3. 24-bit PCM, 16000 Hz (Default)
Choose format (1-3, default: 3): 2
Selected: 16-bit PCM, 16000 Hz
Pause between turns in seconds (default: 0.5): 3
Using pause duration: 3.0s

Output filename (default: narration.wav): long-transcript-3-second-16-bit.wav

============================================================
Exporting transcript to audio file...
Format: 16-bit PCM, 16000 Hz, Mono
Default pause: 3.0s between turns
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
✓ Audio file saved: long-transcript-3-second-16-bit.wav
  Format: 16-bit PCM, 16000 Hz, Mono
  Duration: 397.7 seconds
  File size: 12426.7 KB
============================================================
```