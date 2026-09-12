"""
World & Environment State Tracker for JARVIS General Task Reasoning.
Maintains grounded real-time representation of system context, active applications,
window focus, UI accessibility semantics, browser DOM, OCR data, and privacy boundaries.
"""

import time
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from jarvis.core.hardware import HardwareDetector
from jarvis.computer.windows.window import WindowsWindowManager
from jarvis.computer.base import WindowInfo

logger = logging.getLogger("jarvis.core.reasoning.world_state")


class EnvironmentState(BaseModel):
    """Snapshot of system environment resources and capability status."""
    os_name: str = "Windows"
    cpu_count: int = 4
    total_ram_gb: float = 8.0
    active_profile: str = "LOW"
    audio_available: bool = True
    browser_available: bool = True
    ocr_available: bool = True
    active_window_title: str = ""
    active_process_name: str = ""
    timestamp: float = Field(default_factory=time.time)


class UIStateSnapshot(BaseModel):
    """Perception snapshot of visible interface elements and focus."""
    window_title: str = ""
    process_name: str = ""
    accessibility_elements_count: int = 0
    visible_headings: List[str] = Field(default_factory=list)
    visible_buttons: List[str] = Field(default_factory=list)
    visible_inputs: List[str] = Field(default_factory=list)
    has_modal_dialog: bool = False
    privacy_sensitive: bool = False
    confidence: float = 1.0


class WorldState:
    """
    Grounded World State engine maintaining real-time environment perception,
    execution context, and history for general task reasoning.
    """

    _instance: Optional["WorldState"] = None

    @classmethod
    def get_instance(cls) -> "WorldState":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.action_history: List[Dict[str, Any]] = []
        self.environment: EnvironmentState = self._capture_environment()
        self.latest_snapshot: Optional[UIStateSnapshot] = None
        self.active_context: Dict[str, Any] = {}

    def _capture_environment(self) -> EnvironmentState:
        """Captures hardware and active system environment metadata."""
        try:
            h_specs = HardwareDetector.detect()
            active_title = ""
            active_proc = ""
            
            try:
                windows = WindowsWindowManager.list_windows()
                if windows:
                    active_title = windows[0].title
                    active_proc = windows[0].process_name
            except Exception:
                pass

            return EnvironmentState(
                os_name=h_specs.os_name,
                cpu_count=h_specs.cpu_count,
                total_ram_gb=h_specs.total_ram_gb,
                active_profile=h_specs.performance_profile.value,
                audio_available=h_specs.audio_available,
                browser_available=h_specs.browser_available,
                ocr_available=h_specs.ocr_available,
                active_window_title=active_title,
                active_process_name=active_proc,
                timestamp=time.time()
            )
        except Exception as e:
            logger.warning(f"Failed to capture environment state: {e}")
            return EnvironmentState()

    def update_state(self, action_record: Optional[Dict[str, Any]] = None) -> EnvironmentState:
        """Refreshes grounded environment state and logs completed action records."""
        self.environment = self._capture_environment()
        if action_record:
            self.action_history.append({
                "timestamp": time.time(),
                **action_record
            })
            if len(self.action_history) > 100:
                self.action_history = self.action_history[-100:]
        return self.environment

    def update_ui_snapshot(self, snapshot: UIStateSnapshot) -> None:
        """Updates active UI perception snapshot."""
        self.latest_snapshot = snapshot

    def get_grounded_summary(self) -> Dict[str, Any]:
        """Provides concise grounded state summary for task reasoning and plan critic."""
        self.update_state()
        return {
            "os": self.environment.os_name,
            "active_window": self.environment.active_window_title,
            "active_process": self.environment.active_process_name,
            "performance_profile": self.environment.active_profile,
            "recent_actions_count": len(self.action_history),
            "ui_snapshot": self.latest_snapshot.model_dump() if self.latest_snapshot else None,
            "context_keys": list(self.active_context.keys())
        }

    def set_context_variable(self, key: str, value: Any) -> None:
        """Stores a dynamic execution variable in world context."""
        self.active_context[key] = value

    def get_context_variable(self, key: str, default: Any = None) -> Any:
        """Retrieves a dynamic execution variable from world context."""
        return self.active_context.get(key, default)

    def clear_context(self) -> None:
        """Clears working context variables."""
        self.active_context.clear()
