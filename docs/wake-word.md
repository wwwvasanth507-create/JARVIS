# JARVIS Wake-Word Subsystem

## Overview
The **JARVIS Wake-Word Subsystem** (`src/jarvis/voice/wakeword.py`) provides local-first, zero-cloud detection of the wake phrase `"JARVIS"` (and optional `"Hey JARVIS"`).

## 2-Stage CPU Optimization Architecture
To minimize CPU usage while waiting for speech, JARVIS avoids running continuous heavy STT model inference.

```text
Microphone Audio Input (16kHz PCM)
               ↓
    [Stage 1: RMS Energy & VAD Filter]
               ↓ (Speech Detected)
    [Stage 2: Local 2-Stage Wake Detector]
               ↓
  Parsing & Single-Utterance Verification
               ↓
  Transition to WAKEWORD_DETECTED
```

- **Stage 1**: Computes lightweight Root Mean Square (RMS) energy level. Discards silent frames immediately.
- **Stage 2**: Activates local wake phrase detection or ONNX model inference (`models/wakeword/jarvis.onnx`).
- **Single-Utterance Support**: Parses phrases like `"JARVIS, open Chrome and report status"` in a single pass without forcing a pause between wake phrase and command.

## Cooldown & Timeout Protection
- **Cooldown**: Enforces a configurable cooldown period (`cooldown_seconds: 1.0`) after wake detection to prevent duplicate re-triggering.
- **Command Timeout**: If the Boss says `"JARVIS"` but remains silent, command capture times out (`command_timeout_seconds: 8.0`) and returns automatically to `LISTENING_FOR_WAKEWORD`.
- **Fast-Path Acknowledgement**: Immediately synthesizes a deterministic response (`"Yes, Boss?"`) upon wake detection without calling the LLM.

## Model Directory & Fallback
Wake-word models are stored in:
```text
models/
└── wakeword/
    └── jarvis.onnx
```
If no local wake-word model or package is installed, JARVIS degrades gracefully to Push-to-Talk mode (`"Wake word unavailable. Push-to-talk mode remains available."`) without crashing.
