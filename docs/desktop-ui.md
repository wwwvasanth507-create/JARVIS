# JARVIS Desktop UI Shell Architecture

**Document Version**: 1.0  
**Target Desktop OS**: Windows (Primary), Cross-Platform Compatible

---

## 1. Overview

The JARVIS Desktop UI shell provides a modern, responsive, CPU-friendly graphical user interface (`src/jarvis/ui/`) communicating with the single authoritative `JARVISApp` runtime (`src/jarvis/app.py`).

```text
User (Boss)
  ↓
Tkinter Desktop Window / System Tray (src/jarvis/ui/desktop_app.py)
  ↓
UI Event Pump & Queue (queue.Queue / root.after)
  ↓
JARVISApp Single Authoritative Runtime (src/jarvis/app.py)
  ↓
Orchestrator → Security → Planner → Tools → Verification → Response
```

---

## 2. Key Components

- **`HeaderView`**: App title, status indicator (`ONLINE`, `DEGRADED`, `OFFLINE`), hardware performance mode badge, microphone state, model state.
- **`ConversationView`**: Scrollable chat timeline rendering Boss commands, JARVIS answers, progress steps (`Understanding...`, `Planning...`, `Executing...`, `Verifying...`), and error cards.
- **`InputView`**: Input entry box, Send button, Universal Stop/Cancel button, Clear Conversation button, Voice toggle button, Wake-Word toggle (`Wake Word: ON` / `OFF`).
- **`StatusView`**: Real-time memory footprint (RAM MB), CPU profile, active task, scheduler status.
- **`SystemTrayManager`**: System tray icon in Windows Notification Area with context menu (`Open JARVIS`, `Doctor`, `Capabilities`, `Exit`), window minimize-to-tray, and notification balloon popups.
- **`SingleInstanceLock`**: Enforces single-instance application execution via Windows Named Mutex.
- **`ConfirmationDialog`**: GUI modal for high-risk action authorization.
- **`HumanInterventionDialog`**: Surfacing `HumanInterventionRequiredError` (CAPTCHA, user choices).
- **`SettingsWindow`**: User preferences backed by YAML configuration.

---

## 3. Design Aesthetics & Visual System

- **Primary Background**: Obsidian `#0d1117`
- **Surface Container**: Slate `#161b22`
- **Input Background**: Charcoal `#21262d`
- **Borders**: `#30363d`
- **Cyan Accent**: `#58a6ff`
- **Status Colors**: Ready Green `#238636`, Warning Yellow `#d29922`, Error Red `#f85149`, Voice Purple `#a371f7`
