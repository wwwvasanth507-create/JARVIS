# JARVIS Audio Subsystem & Ownership Architecture

## Audio Ownership Lock Manager
To prevent background wake-word listening, STT command recording, and Push-to-Talk from colliding over microphone input resources, access is governed by the `AudioOwnershipManager` (`src/jarvis/voice/ownership.py`).

### Ownership Lifecycle
1. **Wakeword Listening**: `AudioOwnershipManager.acquire("wakeword")`
2. **Wake Word Detected**: `AudioOwnershipManager.release("wakeword")`
3. **Fast-Path Ack**: Predefined response spoken via TTS
4. **Command Recording**: `AudioOwnershipManager.acquire("stt")`
5. **Command Finish**: `AudioOwnershipManager.release("stt")` -> `acquire("wakeword")`

## Interruption & Barge-In Architecture
When JARVIS is in the `SPEAKING` state:
- Calling `VoiceManager.interrupt()` or `stop_speech()` immediately halts active TTS audio output via `pyttsx3.stop()` and `sounddevice.stop()`.
- The state machine immediately transitions back to `LISTENING_FOR_WAKEWORD`.

## Hardware Recovery & Safety
- Audio streams are captured in ephemeral memory buffers.
- Disconnected audio devices are detected gracefully without crashing the core system.
- If audio input fails, Push-to-Talk or text chat remain active.
