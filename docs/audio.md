# JARVIS Audio Infrastructure & Hardware Management

## Device Discovery
Audio hardware discovery is managed via `AudioDeviceDiscovery` in `src/jarvis/voice/audio_device.py`.

### Microphone Discovery
- Queries available system input devices using `sounddevice.query_devices()`.
- Identifies the default input microphone and sample rate (16kHz standard for STT).

### Speaker Discovery
- Queries available output devices and default output speaker.

## Audio Processing Pipeline
```text
Microphone (16kHz Mono PCM)
        ↓
Voice Activity Detector (RMS Energy Filter)
        ↓
Local Speech-to-Text (Whisper int8 on CPU)
        ↓
Transcribed Text
        ↓
JARVIS Brain
        ↓
Response Text Stream
        ↓
Local Text-to-Speech (pyttsx3 / Windows SAPI5 Female Voice)
        ↓
Speaker Output
```

## Resource Cleanup & Safety
- Audio streams are recorded in ephemeral byte buffers.
- Microphones are automatically released immediately after recording completes.
- No temporary audio files are stored permanently on disk.
