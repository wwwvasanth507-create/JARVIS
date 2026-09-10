# Supervision Recovery & User Takeover

## User Takeover & Safe Handoff (`src/jarvis/system/user_takeover.py`)
Subscribes to system events (`WINDOW_FOCUSED`) and detects manual Boss interactions in active windows.

### Safe Handoff Behavior:
- Automatically pauses conflicting background tasks with a clean notification ("Safe Handoff") rather than fighting the user for window control or overwriting user inputs.
