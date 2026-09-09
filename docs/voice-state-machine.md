# JARVIS Voice & Privacy State Machine

## Overview
The **Voice State Machine** (`src/jarvis/voice/state_machine.py`) manages all operational listening states, enforces valid state transitions, logs audit events, and exposes explicit privacy labels to the user.

## Microphone Privacy States
| State | Privacy Label | Description |
|-------|---------------|-------------|
| `MICROPHONE_OFF` | `MIC OFF` | Microphone hardware is disabled |
| `LISTENING_FOR_WAKEWORD` | `MIC LISTENING (Wake Word Only)` | Low-power Stage 1 VAD & wake detection active |
| `WAKEWORD_DETECTED` | `MIC ACTIVE (Wake Detected)` | Wake phrase identified; preparing command capture |
| `LISTENING_FOR_COMMAND` | `MIC ACTIVE (Listening for Command)` | Capturing command audio from Boss |
| `PROCESSING` | `MIC BUSY (Processing Command)` | STT transcription & LLM generation active |
| `SPEAKING` | `MIC STANDBY (Speaking Response)` | TTS response active; speech interruption enabled |
| `PAUSED` | `MIC PAUSED` | Listening paused by user |
| `ERROR` | `MIC ERROR` | Audio hardware error encountered |

## Valid State Transition Diagram
```text
                    ┌─────────────────────┐
                    │   MICROPHONE_OFF    │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ LISTENING_FOR_WAKE  │◄────────────┐
                    └──────────┬──────────┘             │
                               │                        │
                         Wake detected                  │
                               │                        │
                               ▼                        │
                    ┌─────────────────────┐             │
                    │ LISTENING_FOR_CMD   │             │
                    └──────────┬──────────┘             │
                               │                        │
                         Speech finished / Timeout      │
                               │                        │
                               ▼                        │
                    ┌─────────────────────┐             │
                    │    PROCESSING       │─────────────┤
                    └──────────┬──────────┘             │
                               │                        │
                               ▼                        │
                    ┌─────────────────────┐             │
                    │     SPEAKING        │─────────────┘
                    └─────────────────────┘ (Done or Interrupted)
```

## Logging Audit Events
State transitions automatically emit structured audit events:
- `WAKEWORD_STARTED`
- `WAKEWORD_DETECTED`
- `COMMAND_LISTENING_STARTED`
- `COMMAND_LISTENING_STOPPED`
- `VOICE_PROCESSING_STARTED`
- `VOICE_PROCESSING_COMPLETED`
- `TTS_STARTED`
- `TTS_STOPPED`
- `WAKEWORD_PAUSED`
- `WAKEWORD_RESUMED`
