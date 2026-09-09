# JARVIS Voice Subsystem Architecture

## Overview
The **JARVIS Voice Subsystem** (`src/jarvis/voice/`) delivers local-first, zero-cloud speech recognition (STT) and speech synthesis (TTS) designed specifically for CPU-only computers.

## Core Design Principles
1. **Local-Only Processing**: All audio input and synthesis occur locally on device. No microphone recordings leave the machine.
2. **CPU-First Efficiency**: Avoids continuous heavy model inference while idle by using Voice Activity Detection (VAD) and Push-to-Talk fallback.
3. **Decoupled Architecture**: The core JARVIS Brain remains ignorant of input modality. typed inputs and speech transcriptions both map to `UserMessage` objects.
4. **Graceful Degradation**: Audio component failures (missing mic, missing dependencies, TTS errors) automatically degrade to text chat without interrupting the application.

## Subsystem Components
- **`AudioDeviceDiscovery`** (`audio_device.py`): Enumerates microphones and speakers.
- **`AudioInputManager` / `AudioOutputManager`** (`audio_device.py`): Handles PCM recording, playback, and resource release.
- **`VoiceActivityDetector`** (`vad.py`): Lightweight RMS energy-based VAD to prevent idle CPU churn.
- **`SpeechRecognizer` / `LocalWhisperSTT`** (`stt.py`): Local speech-to-text using CPU-quantized Whisper models (`tiny`/`base`/`small`). Supports auto language detection including English, Tamil, and Tamil-English code switching.
- **`TextToSpeech` / `PyTTSx3TextToSpeech`** (`tts.py`): Local TTS synthesis using native OS voices (configured for female voices like Microsoft Zira Desktop / Microsoft Hazel Desktop).
- **`WakeWordDetector`** (`wakeword.py`): Abstract interface prepared for continuous wake-word detection (PROMPT 004).
- **`VoiceManager`** (`manager.py`): Central orchestrator managing modes (`chat`, `voice`, `hybrid`) and sentence-level streaming synthesis.

## Operational Modes
- **Chat**: Text input -> Brain -> Text output.
- **Voice**: Speech input -> STT -> Brain -> TTS output.
- **Hybrid**: Text or Speech input -> Brain -> Text + TTS output.
