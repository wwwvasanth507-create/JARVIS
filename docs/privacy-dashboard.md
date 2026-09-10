# System Privacy Dashboard

## Privacy Visibility (`src/jarvis/system/privacy_dashboard.py`)
Provides real-time state tracking and UI visibility across 8 capability categories:
- `microphone`
- `wake_word`
- `screen_access`
- `browser_access`
- `filesystem_access`
- `background_monitors`
- `memory_access`
- `network_access`

Each capability displays its `enabled/disabled` state, audit reason, and timestamp of last activity.
