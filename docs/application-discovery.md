# Application Discovery & Cache Indexing

JARVIS uses fast, OS-native discovery mechanisms to locate installed desktop applications without full disk scans.

## Discovery Locations

- **Windows**: Start Menu Shortcuts (`%APPDATA%` and `%ALLUSERSPROFILE%`), App Paths Registry keys, `C:\Program Files`, `%LOCALAPPDATA%\Programs`.
- **Linux**: `/usr/share/applications/*.desktop`, `~/.local/share/applications/*.desktop`.
- **macOS**: `/Applications/*.app`, `~/Applications/*.app`.

## Cache Architecture

- Discovered applications are stored in `data/indexes/applications.json`.
- Subsequent registry lookups read the lightweight cache to maintain sub-millisecond query responses.
- Discovery is refreshed on demand or when applications are updated.
