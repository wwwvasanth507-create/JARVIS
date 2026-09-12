# Live Boss Supervision & Desktop Telemetry Guide (Prompt 026)

## Overview
JARVIS provides an always-available, reactive **Live Task Monitor** widget integrated directly into the desktop UI (`src/jarvis/ui/live_monitor.py`). It gives the Boss complete real-time visibility into task hierarchy, active window, action rationale, target element, confidence score, risk level, payload preview, and next intended action without exposing private internal chain-of-thought.

---

## Live Monitor Display Fields

```
======================================================
           LIVE TASK EXECUTION MONITOR
======================================================
  TASK        : Send report to Vasanth
  GOAL        : SEND_EMAIL
  SUBTASK     : Compose Email Message
  APP / WINDOW: Browser -> Webmail
  ACTION      : TYPE
  TARGET      : To: input field
  CONFIDENCE  : 98%
  STATUS      : EXECUTING
  NEXT ACTION : Type vasanth@local.computer
======================================================
```

---

## Desktop Telemetry Features

1. **Active Task & Subtask Tracking**: Shows current high-level goal and individual execution step title.
2. **Active App & Target Element Grounding**: Displays active application process/window and identified interactive target control.
3. **Confidence Score**: Real-time confidence metric (e.g. 98%).
4. **Governed Confirmation Requests**: Prominently displays high-risk approval requests when policy requires Boss authorization before proceeding.
5. **Soft Interruption & Pause Controls**: Supports pause/resume and human takeover when the Boss interacts with input devices.

---

## Technical Integration

```python
from jarvis.ui.live_monitor import LiveTaskMonitorWidget

# Instantiate in Tkinter UI layout
monitor = LiveTaskMonitorWidget(parent=app_frame)
monitor.pack(fill="x", padx=10, pady=5)

# Update telemetry on task execution events
monitor.update_task_state({
    "task": "Extract report and send summary",
    "goal": "CROSS_APP_WORKFLOW",
    "subtask": "Extract Document Text",
    "app": "Notepad -> monthly_report.txt",
    "action": "READ_DATA",
    "target": "Text content area",
    "confidence": 0.95,
    "status": "RUNNING",
    "next_action": "Compose email draft to Vasanth"
})
```
