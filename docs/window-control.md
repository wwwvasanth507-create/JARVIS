# JARVIS Window Management Subsystem

## Overview
The **JARVIS Window Manager** (`src/jarvis/computer/windows/window.py`) enumerates active desktop windows, retrieves window metadata, and controls window focus, minimization, maximization, restoration, and closing.

## Window Capabilities
- **`list_windows()`**: Enumerates visible top-level windows using Win32 `EnumWindows` and `psutil`, returning window title, process ID, bounds, and state (`is_active`, `is_minimized`, `is_maximized`).
- **`get_active_window()`**: Queries current foreground window.
- **`focus_window(title_or_hwnd)`**: Restores window if minimized and calls `SetForegroundWindow`.
- **`minimize_window(title_or_hwnd)`**: Calls `ShowWindow(hwnd, SW_MINIMIZE)`.
- **`maximize_window(title_or_hwnd)`**: Calls `ShowWindow(hwnd, SW_MAXIMIZE)`.
- **`restore_window(title_or_hwnd)`**: Calls `ShowWindow(hwnd, SW_RESTORE)`.
- **`close_window(title_or_hwnd)`**: Posts `WM_CLOSE` message to target window handle.

## Registered Window Tools
| Tool Identifier | Description | Permission | Risk Level |
|-----------------|-------------|------------|------------|
| `computer.active_window` | Gets metadata for active foreground window | `SCREEN_READ` | `LOW` |
| `computer.list_windows` | Lists visible top-level windows | `SCREEN_READ` | `LOW` |
| `computer.focus_window` | Focuses target window | `COMPUTER_CONTROL` | `LOW` |
| `computer.minimize_window` | Minimized window | `COMPUTER_CONTROL` | `LOW` |
| `computer.maximize_window` | Maximizes window | `COMPUTER_CONTROL` | `LOW` |
| `computer.restore_window` | Restores window | `COMPUTER_CONTROL` | `LOW` |
| `computer.close_window` | Closes window | `APPLICATION_CONTROL` | `MEDIUM` |
