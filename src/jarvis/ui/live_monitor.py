"""
Live Boss Supervision & Execution State Monitor Widget for JARVIS Desktop UI.
Provides real-time visibility into task hierarchy, active window, action rationale,
confidence score, risk level, payload preview, and next intended action.
"""

import time
import logging
import tkinter as tk
from tkinter import ttk
from typing import Dict, Any, Optional

logger = logging.getLogger("jarvis.ui.live_monitor")


class LiveTaskMonitorWidget(ttk.Frame):
    """
    Reactive Tkinter widget displaying live task execution telemetry,
    subtask state, active window, confidence score, and verification checkpoints.
    """

    def __init__(self, parent=None, **kwargs):
        if parent is not None:
            super().__init__(parent, **kwargs)
        else:
            try:
                super().__init__(**kwargs)
            except Exception:
                pass

        self._state_cache: Dict[str, Any] = {
            "task": "Idle",
            "goal": "None",
            "subtask": "None",
            "app": "None",
            "action": "None",
            "target": "None",
            "confidence": 1.0,
            "status": "READY",
            "next": "None"
        }

        # Header Title
        title_label = ttk.Label(self, text="LIVE TASK EXECUTION MONITOR", font=("Helvetica", 10, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 4))

        # Metric Labels
        self._labels: Dict[str, ttk.Label] = {}

        metrics = [
            ("task", "TASK"),
            ("goal", "GOAL"),
            ("subtask", "SUBTASK"),
            ("app", "APP / WINDOW"),
            ("action", "ACTION"),
            ("target", "TARGET"),
            ("confidence", "CONFIDENCE"),
            ("status", "STATUS"),
            ("next", "NEXT ACTION"),
        ]

        for idx, (key, label_text) in enumerate(metrics, start=1):
            lbl_key = ttk.Label(self, text=f"{label_text}:", font=("Helvetica", 8, "bold"))
            lbl_key.grid(row=idx, column=0, sticky="w", padx=(0, 6), pady=1)

            lbl_val = ttk.Label(self, text="Idle", font=("Helvetica", 8))
            lbl_val.grid(row=idx, column=1, sticky="w", pady=1)
            self._labels[key] = lbl_val

    def update_telemetry(
        self,
        task: str = "Idle",
        goal: str = "None",
        subtask: str = "None",
        app_window: str = "None",
        action: str = "None",
        target: str = "None",
        confidence: float = 1.0,
        status: str = "READY",
        next_action: str = "None"
    ) -> None:
        """Updates live execution telemetry values reactively."""
        self._state_cache = {
            "task": task,
            "goal": goal,
            "subtask": subtask,
            "app": app_window,
            "action": action,
            "target": target,
            "confidence": confidence,
            "status": status,
            "next": next_action
        }
        try:
            if "task" in self._labels:
                self._labels["task"].config(text=task[:50])
            if "goal" in self._labels:
                self._labels["goal"].config(text=goal[:50])
            if "subtask" in self._labels:
                self._labels["subtask"].config(text=subtask[:50])
            if "app" in self._labels:
                self._labels["app"].config(text=app_window[:45])
            if "action" in self._labels:
                self._labels["action"].config(text=action[:45])
            if "target" in self._labels:
                self._labels["target"].config(text=target[:45])
            if "confidence" in self._labels:
                self._labels["confidence"].config(text=f"{confidence * 100:.0f}%")
            if "status" in self._labels:
                self._labels["status"].config(text=status)
            if "next" in self._labels:
                self._labels["next"].config(text=next_action[:50])
        except Exception as e:
            logger.debug(f"Telemetry update exception: {e}")

    def update_task_state(self, state_dict: Dict[str, Any]) -> None:
        self.update_telemetry(
            task=state_dict.get("task", "Idle"),
            goal=state_dict.get("goal", "None"),
            subtask=state_dict.get("subtask", "None"),
            app_window=state_dict.get("app", "None"),
            action=state_dict.get("action", "None"),
            target=state_dict.get("target", "None"),
            confidence=state_dict.get("confidence", 1.0),
            status=state_dict.get("status", "READY"),
            next_action=state_dict.get("next_action", "None")
        )

    def get_current_summary(self) -> Dict[str, Any]:
        return dict(self._state_cache)
