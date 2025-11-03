"""
Transcript Narrator Example

This app narrates transcripts using different TTS voices for different speakers.
"""

import sys
import json
import time
import wave
import tempfile
import os
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from piper import PiperVoice
    import numpy as np
except ImportError:
    print("Error: Required packages not installed.")
    print("Run: pip install piper-tts numpy")
    sys.exit(1)


class AudioFormat:
    """Audio format configuration."""
    
    # Predefined formats
    FORMAT_16BIT_22050 = "16bit_22050hz"  # Original: 16-bit PCM @ 22.05 kHz
    FORMAT_16BIT_16000 = "16bit_16000hz"  # 16-bit PCM @ 16 kHz
    FORMAT_24BIT_16000 = "24bit_16000hz"  # 24-bit PCM @ 16 kHz
    
    def __init__(self, format_name: str = FORMAT_24BIT_16000):
        self.format_name = format_name
        
        if format_name == self.FORMAT_16BIT_22050:
            self.bit_depth = 16
            self.sample_rate = 22050
            self.sample_width = 2  # bytes
        elif format_name == self.FORMAT_16BIT_16000:
            self.bit_depth = 16
            self.sample_rate = 16000
            self.sample_width = 2  # bytes
        elif format_name == self.FORMAT_24BIT_16000:
            self.bit_depth = 24
            self.sample_rate = 16000
            self.sample_width = 3  # bytes
        else:
            raise ValueError(f"Unknown format: {format_name}")
    
    def __str__(self):
        return f"{self.bit_depth}-bit PCM, {self.sample_rate} Hz, Mono"
    
    @staticmethod
    def get_format_options():
        """Get list of available format options."""
        return {
            "1": (AudioFormat.FORMAT_16BIT_22050, "16-bit PCM, 22050 Hz (Original)"),
            "2": (AudioFormat.FORMAT_16BIT_16000, "16-bit PCM, 16000 Hz"),
            "3": (AudioFormat.FORMAT_24BIT_16000, "24-bit PCM, 16000 Hz (Default)"),
        }


class VoiceManager:
    """Manages multiple Piper TTS voices."""
    
    def __init__(self, models_dir: Path):
        self.models_dir = models_dir
        self.voices: Dict[str, PiperVoice] = {}
        self.available_voices = self._discover_voices()
        
    def _discover_voices(self) -> Dict[str, Path]:
        """Discover available voice models."""
        voices = {}
        
        if not self.models_dir.exists():
            print(f"Warning: Models directory not found: {self.models_dir}")
            return voices
        
        for model_file in self.models_dir.glob("*.onnx"):
            if model_file.stem.endswith(".onnx"):
                continue  # Skip .onnx.json files
            
            config_file = model_file.parent / f"{model_file.name}.json"
            if config_file.exists():
                voice_name = model_file.stem
                voices[voice_name] = model_file
                print(f"Found voice: {voice_name}")
        
        return voices
    
    def load_voice(self, voice_name: str) -> Optional[PiperVoice]:
        """Load a specific voice model."""
        if voice_name in self.voices:
            return self.voices[voice_name]
        
        if voice_name not in self.available_voices:
            print(f"Warning: Voice '{voice_name}' not found")
            return None
        
        try:
            model_path = self.available_voices[voice_name]
            config_path = model_path.parent / f"{model_path.name}.json"
            
            voice = PiperVoice.load(str(model_path), str(config_path))
            self.voices[voice_name] = voice
            print(f"Loaded voice: {voice_name}")
            return voice
            
        except Exception as e:
            print(f"Error loading voice '{voice_name}': {e}")
            return None
    
    def get_voice(self, voice_name: str) -> Optional[PiperVoice]:
        """Get a voice, loading it if necessary."""
        if voice_name not in self.voices:
            return self.load_voice(voice_name)
        return self.voices[voice_name]


class TranscriptNarrator:
    """Narrates transcripts with different voices for different speakers."""
    
    def __init__(self, transcript_path: str):
        self.transcript_path = Path(transcript_path)
        self.transcript_data = None
        self.voice_manager = None
        self.speaker_voices: Dict[str, str] = {}
        
        # Default voice assignments (can be customized)
        self.default_voice_map = {
            "Clinician": "en_US-amy-medium",
            "Patient": "en_US-ryan-high",
            "Doctor": "en_US-lessac-medium",
            "Nurse": "en_US-amy-medium",
            "Other": "en_US-ryan-high",
        }
        
        # Initialize
        self._load_transcript()
        self._setup_voices()
    
    def _load_transcript(self):
        """Load transcript from JSON file."""
        try:
            with open(self.transcript_path, 'r') as f:
                self.transcript_data = json.load(f)
            
            print(f"✓ Loaded transcript: {self.transcript_path.name}")
            
            # Validate structure
            if "transcript" not in self.transcript_data:
                raise ValueError("Invalid transcript format: missing 'transcript' key")
            
            if "turns" not in self.transcript_data["transcript"]:
                raise ValueError("Invalid transcript format: missing 'turns' key")
            
            turns = self.transcript_data["transcript"]["turns"]
            print(f"  {len(turns)} turns found")
            
        except FileNotFoundError:
            print(f"Error: Transcript file not found: {self.transcript_path}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in transcript file: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"Error loading transcript: {e}")
            sys.exit(1)
    
    def _setup_voices(self):
        """Set up TTS voices."""
        models_dir = Path(__file__).parent.parent / "tts" / "models"
        self.voice_manager = VoiceManager(models_dir)
        
        if not self.voice_manager.available_voices:
            print("\nError: No TTS voice models found!")
            print(f"Expected location: {models_dir}")
            print("Run: python tts/download_models.py")
            sys.exit(1)
        
        print(f"\n✓ Available voices: {list(self.voice_manager.available_voices.keys())}")
        
        # Assign voices to speakers
        turns = self.transcript_data["transcript"]["turns"]
        speakers = set(turn["speaker"] for turn in turns)
        
        print(f"\nSpeakers in transcript: {speakers}")
        
        # Auto-assign voices to speakers
        available_voice_list = list(self.voice_manager.available_voices.keys())
        
        for i, speaker in enumerate(sorted(speakers)):
            if speaker in self.default_voice_map:
                voice = self.default_voice_map[speaker]
                if voice in self.voice_manager.available_voices:
                    self.speaker_voices[speaker] = voice
                else:
                    # Fallback to first available voice
                    self.speaker_voices[speaker] = available_voice_list[i % len(available_voice_list)]
            else:
                # Assign voices round-robin
                self.speaker_voices[speaker] = available_voice_list[i % len(available_voice_list)]
        
        print("\nVoice assignments:")
        for speaker, voice in self.speaker_voices.items():
            print(f"  {speaker} → {voice}")
        
        # Pre-load all required voices
        print("\nLoading voices...")
        for voice_name in set(self.speaker_voices.values()):
            self.voice_manager.load_voice(voice_name)
    
    def synthesize_to_file(self, text: str, voice_name: str, audio_format: AudioFormat = None) -> Optional[str]:
        """Synthesize speech and save to temporary file."""
        if audio_format is None:
            audio_format = AudioFormat(AudioFormat.FORMAT_24BIT_16000)
        
        voice = self.voice_manager.get_voice(voice_name)
        if not voice:
            return None
        
        try:
            # Synthesize audio
            audio_chunks = []
            sample_rate = None
            
            for audio_chunk in voice.synthesize(text):
                if sample_rate is None and hasattr(audio_chunk, 'sample_rate'):
                    sample_rate = audio_chunk.sample_rate
                
                if hasattr(audio_chunk, 'audio_float_array'):
                    audio_data = audio_chunk.audio_float_array
                    if isinstance(audio_data, np.ndarray) and audio_data.size > 0:
                        audio_chunks.append(audio_data.flatten())
            
            if not audio_chunks:
                return None
            
            # Concatenate audio
            audio_data = np.concatenate(audio_chunks)
            
            # Resample if needed
            if sample_rate and sample_rate != audio_format.sample_rate:
                try:
                    from scipy import signal
                    num_samples = int(len(audio_data) * audio_format.sample_rate / sample_rate)
                    audio_data = signal.resample(audio_data, num_samples)
                except ImportError:
                    # If scipy not available and rates don't match, use original rate
                    if sample_rate != audio_format.sample_rate:
                        audio_format.sample_rate = sample_rate
            
            # Clip audio
            audio_clipped = np.clip(audio_data, -1.0, 1.0)
            
            # Convert based on bit depth
            if audio_format.bit_depth == 16:
                # 16-bit PCM
                audio_int = (audio_clipped * 32767).astype(np.int16)
                audio_bytes = audio_int.tobytes()
            elif audio_format.bit_depth == 24:
                # 24-bit PCM
                audio_int24 = (audio_clipped * 8388607).astype(np.int32)
                audio_bytes_4 = audio_int24.tobytes()
                
                # Extract 3 bytes per sample (little-endian)
                audio_bytes = bytearray()
                for i in range(0, len(audio_bytes_4), 4):
                    audio_bytes.extend(audio_bytes_4[i:i+3])
                audio_bytes = bytes(audio_bytes)
            else:
                raise ValueError(f"Unsupported bit depth: {audio_format.bit_depth}")
            
            # Write to temporary WAV file
            temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            temp_path = temp_file.name
            temp_file.close()
            
            with wave.open(temp_path, "wb") as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(audio_format.sample_width)
                wav_file.setframerate(audio_format.sample_rate)
                wav_file.writeframes(audio_bytes)
            
            return temp_path
            
        except Exception as e:
            print(f"Error synthesizing audio: {e}")
            return None
    
    def play_audio_file(self, audio_path: str):
        """Play audio file using system audio player."""
        try:
            if sys.platform == 'darwin':  # macOS
                subprocess.run(['afplay', audio_path], 
                             stdout=subprocess.DEVNULL, 
                             stderr=subprocess.DEVNULL,
                             check=False)
            elif sys.platform == 'win32':  # Windows
                subprocess.run(['powershell', '-c', 
                              f'(New-Object Media.SoundPlayer "{audio_path}").PlaySync()'],
                             stdout=subprocess.DEVNULL, 
                             stderr=subprocess.DEVNULL,
                             check=False)
            else:  # Linux
                subprocess.run(['aplay', audio_path], 
                             stdout=subprocess.DEVNULL, 
                             stderr=subprocess.DEVNULL,
                             check=False)
        except Exception as e:
            print(f"Error playing audio: {e}")
    
    def narrate_turn(self, turn: Dict, skip_empty: bool = True):
        """Narrate a single turn of the transcript."""
        speaker = turn["speaker"]
        text = turn["text"]
        index = turn["index"]
        
        # Skip empty turns if requested
        if skip_empty and not text.strip():
            print(f"\n[Turn {index}] {speaker}: (empty - skipped)")
            return
        
        voice_name = self.speaker_voices.get(speaker, list(self.speaker_voices.values())[0])
        
        # Display turn info
        print(f"\n[Turn {index}] {speaker} ({voice_name}):")
        print(f"  \"{text}\"")
        
        # Synthesize and play
        audio_path = self.synthesize_to_file(text, voice_name)
        if audio_path:
            self.play_audio_file(audio_path)
            
            # Clean up temp file
            try:
                os.unlink(audio_path)
            except:
                pass
        else:
            print("  ⚠️  Failed to synthesize audio")
    
    def narrate_full_transcript(self, pause_between_turns: float = 0.5, skip_empty: bool = True):
        """Narrate the entire transcript."""
        turns = self.transcript_data["transcript"]["turns"]
        
        print("\n" + "="*60)
        print("Starting transcript narration...")
        print(f"Default pause: {pause_between_turns}s between turns")
        print("="*60)
        
        for i, turn in enumerate(turns):
            # Skip empty turns if requested
            if skip_empty and not turn.get("text", "").strip():
                continue
            
            self.narrate_turn(turn, skip_empty=skip_empty)
            
            # Check for custom pause in turn data
            custom_pause = turn.get("pause_after", None)
            pause_duration = custom_pause if custom_pause is not None else pause_between_turns
            
            # Pause between turns (but not after the last turn)
            if i < len(turns) - 1 and pause_duration > 0:
                time.sleep(pause_duration)
        
        print("\n" + "="*60)
        print("Transcript narration complete!")
        print("="*60)
    
    def export_to_audio_file(self, output_path: str, pause_between_turns: float = 0.5, skip_empty: bool = True, audio_format: AudioFormat = None):
        """Export entire transcript to a single audio file."""
        if audio_format is None:
            audio_format = AudioFormat(AudioFormat.FORMAT_24BIT_16000)
        
        turns = self.transcript_data["transcript"]["turns"]
        
        print("\n" + "="*60)
        print("Exporting transcript to audio file...")
        print(f"Format: {audio_format}")
        print(f"Default pause: {pause_between_turns}s between turns")
        print("="*60)
        
        all_audio_chunks = []
        sample_rate = None
        
        for i, turn in enumerate(turns):
            speaker = turn["speaker"]
            text = turn["text"]
            index = turn["index"]
            
            # Skip empty turns if requested
            if skip_empty and not text.strip():
                print(f"[Turn {index}] {speaker}: (empty - skipped)")
                continue
            
            voice_name = self.speaker_voices.get(speaker, list(self.speaker_voices.values())[0])
            voice = self.voice_manager.get_voice(voice_name)
            
            if not voice:
                print(f"  ⚠️  Skipping turn {index} - voice not available")
                continue
            
            print(f"[Turn {index}] {speaker}: \"{text[:50]}...\"")
            
            try:
                # Synthesize audio for this turn
                audio_chunks = []
                
                for audio_chunk in voice.synthesize(text):
                    if sample_rate is None and hasattr(audio_chunk, 'sample_rate'):
                        sample_rate = audio_chunk.sample_rate
                    
                    if hasattr(audio_chunk, 'audio_float_array'):
                        audio_data = audio_chunk.audio_float_array
                        if isinstance(audio_data, np.ndarray) and audio_data.size > 0:
                            audio_chunks.append(audio_data.flatten())
                
                if audio_chunks:
                    turn_audio = np.concatenate(audio_chunks)
                    all_audio_chunks.append(turn_audio)
                    
                    # Check for custom pause in turn data
                    custom_pause = turn.get("pause_after", None)
                    pause_duration = custom_pause if custom_pause is not None else pause_between_turns
                    
                    # Add pause between turns (but not after the last turn)
                    if pause_duration > 0 and i < len(turns) - 1:
                        silence_samples = int((sample_rate or 22050) * pause_duration)
                        silence = np.zeros(silence_samples, dtype=np.float32)
                        all_audio_chunks.append(silence)
                        if custom_pause is not None:
                            print(f"  (custom pause: {pause_duration}s)")
                
            except Exception as e:
                print(f"  ⚠️  Error processing turn {index}: {e}")
                continue
        
        if not all_audio_chunks:
            print("\n❌ No audio data generated")
            return False
        
        try:
            # Concatenate all audio
            final_audio = np.concatenate(all_audio_chunks)
            
            # Resample if needed
            if sample_rate and sample_rate != audio_format.sample_rate:
                try:
                    from scipy import signal
                    num_samples = int(len(final_audio) * audio_format.sample_rate / sample_rate)
                    final_audio = signal.resample(final_audio, num_samples)
                    print(f"  Resampled from {sample_rate} Hz to {audio_format.sample_rate} Hz")
                except ImportError:
                    print(f"  Warning: scipy not installed, keeping original sample rate {sample_rate} Hz")
                    audio_format.sample_rate = sample_rate
            
            # Clip audio
            audio_clipped = np.clip(final_audio, -1.0, 1.0)
            
            # Convert based on bit depth
            if audio_format.bit_depth == 16:
                # 16-bit PCM
                audio_int = (audio_clipped * 32767).astype(np.int16)
                audio_bytes = audio_int.tobytes()
            elif audio_format.bit_depth == 24:
                # 24-bit PCM
                audio_int24 = (audio_clipped * 8388607).astype(np.int32)
                audio_bytes_4 = audio_int24.tobytes()
                
                # Extract 3 bytes per sample (little-endian)
                audio_bytes_ba = bytearray()
                for i in range(0, len(audio_bytes_4), 4):
                    audio_bytes_ba.extend(audio_bytes_4[i:i+3])
                audio_bytes = bytes(audio_bytes_ba)
            else:
                raise ValueError(f"Unsupported bit depth: {audio_format.bit_depth}")
            
            # Write to file
            output_path = Path(output_path)
            with wave.open(str(output_path), "wb") as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(audio_format.sample_width)
                wav_file.setframerate(audio_format.sample_rate)
                wav_file.writeframes(audio_bytes)
            
            duration = len(final_audio) / audio_format.sample_rate
            print("\n" + "="*60)
            print(f"✓ Audio file saved: {output_path}")
            print(f"  Format: {audio_format}")
            print(f"  Duration: {duration:.1f} seconds")
            print(f"  File size: {output_path.stat().st_size / 1024:.1f} KB")
            print("="*60)
            
            return True
            
        except Exception as e:
            print(f"\n❌ Error saving audio file: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def interactive_mode(self):
        """Run in interactive mode with controls."""
        turns = self.transcript_data["transcript"]["turns"]
        current_index = 0
        
        print("\n" + "="*60)
        print("Interactive Transcript Narrator")
        print("="*60)
        print("\nControls:")
        print("  [Enter] - Play next turn")
        print("  'r' - Replay current turn")
        print("  'j' - Jump to turn number")
        print("  'a' - Auto-play all remaining turns")
        print("  'q' - Quit")
        print("="*60)
        
        while current_index < len(turns):
            turn = turns[current_index]
            
            print(f"\nCurrent turn: {current_index + 1}/{len(turns)}")
            command = input("Command: ").strip().lower()
            
            if command == 'q':
                print("Exiting...")
                break
            elif command == 'r':
                # Replay current turn
                if current_index > 0:
                    current_index -= 1
                self.narrate_turn(turns[current_index])
                current_index += 1
            elif command == 'j':
                # Jump to turn
                try:
                    turn_num = int(input(f"Jump to turn (1-{len(turns)}): "))
                    if 1 <= turn_num <= len(turns):
                        current_index = turn_num - 1
                    else:
                        print("Invalid turn number")
                except ValueError:
                    print("Invalid input")
            elif command == 'a':
                # Auto-play remaining turns
                while current_index < len(turns):
                    self.narrate_turn(turns[current_index])
                    current_index += 1
                    if current_index < len(turns):
                        time.sleep(0.5)
                break
            else:
                # Play next turn (Enter or any other key)
                self.narrate_turn(turns[current_index])
                current_index += 1
        
        print("\n" + "="*60)
        print("Session complete!")
        print("="*60)


def main():
    """Main function."""
    print("=" * 60)
    print("Transcript Narrator with Multi-Voice TTS")
    print("=" * 60)
    
    # Default transcript path
    default_transcript = Path(__file__).parent / "transcript-1.json"
    
    # Get transcript path from user or use default
    print(f"\nDefault transcript: {default_transcript}")
    transcript_path = input("Enter transcript path (or press Enter for default): ").strip()
    
    if not transcript_path:
        transcript_path = str(default_transcript)
    
    # Create narrator
    try:
        narrator = TranscriptNarrator(transcript_path)
    except Exception as e:
        print(f"Failed to initialize narrator: {e}")
        return
    
    # Choose mode
    print("\nNarration modes:")
    print("1. Auto-play entire transcript")
    print("2. Interactive mode (step through turns)")
    print("3. Export to audio file (no playback)")
    print("4. Export to audio file AND play")
    
    mode = input("Choose mode (1-4): ").strip()
    
    # Get audio format for export modes
    audio_format = None
    if mode in ["3", "4"]:
        print("\nAudio format options:")
        format_options = AudioFormat.get_format_options()
        for key, (format_name, description) in format_options.items():
            print(f"{key}. {description}")
        
        format_choice = input("Choose format (1-3, default: 3): ").strip() or "3"
        if format_choice in format_options:
            format_name, description = format_options[format_choice]
            audio_format = AudioFormat(format_name)
            print(f"Selected: {description}")
        else:
            print("Invalid choice, using default: 24-bit PCM, 16000 Hz")
            audio_format = AudioFormat(AudioFormat.FORMAT_24BIT_16000)
    
    # Get pause duration for modes that need it
    pause_duration = 0.5  # Default
    if mode in ["1", "3", "4"]:
        pause_input = input(f"Pause between turns in seconds (default: 0.5): ").strip()
        if pause_input:
            try:
                pause_duration = float(pause_input)
                print(f"Using pause duration: {pause_duration}s")
            except ValueError:
                print(f"Invalid input, using default: 0.5s")
                pause_duration = 0.5
    
    print()  # Blank line
    
    try:
        if mode == "1":
            narrator.narrate_full_transcript(pause_between_turns=pause_duration, skip_empty=True)
        elif mode == "2":
            narrator.interactive_mode()
        elif mode == "3":
            # Export only
            output_file = input("Output filename (default: narration.wav): ").strip()
            if not output_file:
                output_file = "narration.wav"
            narrator.export_to_audio_file(output_file, pause_between_turns=pause_duration, skip_empty=True, audio_format=audio_format)
        elif mode == "4":
            # Export and play
            output_file = input("Output filename (default: narration.wav): ").strip()
            if not output_file:
                output_file = "narration.wav"
            
            if narrator.export_to_audio_file(output_file, pause_between_turns=pause_duration, skip_empty=True, audio_format=audio_format):
                print("\nNow playing the exported file...")
                time.sleep(1)
                narrator.play_audio_file(output_file)
        else:
            print("Invalid choice. Using auto-play mode.")
            narrator.narrate_full_transcript(pause_between_turns=pause_duration, skip_empty=True)
    except KeyboardInterrupt:
        print("\n\nNarration interrupted by user.")
    except Exception as e:
        print(f"\nError during narration: {e}")


if __name__ == "__main__":
    main()
