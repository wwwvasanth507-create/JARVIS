# JARVIS Application Control Subsystem

## Overview
The **JARVIS Application Subsystem** (`src/jarvis/applications/`) manages desktop application discovery, alias resolution, launching, process observation, and graceful termination.

## Registry & Discovery
- **`config/applications.yaml`**: Pre-configured registry mapping application query aliases (e.g. `"chrome"`, `"google chrome"`, `"browser"`) to executable metadata (`chrome.exe`).
- **`ApplicationRegistry`** ([registry.py](file:///c:/ll/JARVIS/src/jarvis/applications/registry.py)): Resolves query strings and aliases into `ApplicationEntry` objects.
- **`ApplicationDetector`** ([detector.py](file:///c:/ll/JARVIS/src/jarvis/applications/detector.py)): Inspects active system processes via `psutil` and resolves executable file paths in PATH and Program Files.

## Application Lifecycle & Verification
When an application launch or closure is requested:
1. **Resolve**: Query is matched against registry aliases.
2. **Permission Check**: Evaluates `APPLICATION_CONTROL` category permissions.
3. **Execute**:
   - `open_application`: Launches executable via `subprocess.Popen`.
   - `close_application`: Requests graceful window closure (`WM_CLOSE`) or process termination (`force=True`).
4. **Observe & Verify**: Checks running process IDs and visible windows. Returns structured `ComputerActionResult` with `verified=True/False`.

## Registered Application Tools
| Tool Identifier | Description | Permission | Risk Level |
|-----------------|-------------|------------|------------|
| `application.list` | Lists registered application aliases | `APPLICATION_CONTROL` | `LOW` |
| `application.open` | Launches application by name or alias | `APPLICATION_CONTROL` | `LOW` |
| `application.close` | Closes running application | `APPLICATION_CONTROL` | `MEDIUM` |
| `application.is_running` | Checks running status of application | `APPLICATION_CONTROL` | `LOW` |
