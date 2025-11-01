wwlib: How does transcribe.py choose the audio input. This is running on a M4 Mac Mini with a USB audio interface.

Workspace: Collecting workspace informationThe audio input device in transcribe.py is selected implicitly by PyAudio when opening the stream:

```python
stream = p.open(
    format=AUDIO_FORMAT,
    channels=CHANNELS,
    rate=SAMPLE_RATE,
    input=True,
    frames_per_buffer=CHUNK_SAMPLES,
    stream_callback=audio_callback,
)
```

By default, PyAudio uses the system's default input device. If you want to explicitly select your USB audio interface, you need to specify the `input_device_index` parameter in the `p.open()` call. You can list available devices using PyAudio's API:

```python
import pyaudio
p = pyaudio.PyAudio()
for i in range(p.get_device_count()):
    info = p.get_device_info_by_index(i)
    print(f"Device {i}: {info['name']}")
```

Then, set `input_device_index` to the index of your USB device:

```python
stream = p.open(
    format=AUDIO_FORMAT,
    channels=CHANNELS,
    rate=SAMPLE_RATE,
    input=True,
    input_device_index=YOUR_USB_DEVICE_INDEX,  # <-- set this
    frames_per_buffer=CHUNK_SAMPLES,
    stream_callback=audio_callback,
)
```

See `main()` for where to add this.
