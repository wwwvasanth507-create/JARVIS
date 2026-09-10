"""
Capability Registry for JARVIS.

Tracks optional subsystem readiness (Model, Microphone, TTS, Playwright, Browser, OCR, Vision, Scheduler, Desktop Notifications)
and provides status reports without crashing when optional dependencies are missing.
"""

from enum import Enum
import logging
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class CapabilityStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    DEGRADED = "DEGRADED"


class CapabilityItem(BaseModel):
    name: str
    status: CapabilityStatus
    reason: str = "Ready"
    details: Dict[str, Any] = Field(default_factory=dict)


class CapabilityRegistry:
    """Registry tracking system capabilities and status for diagnostic reporting."""

    def __init__(self):
        self._capabilities: Dict[str, CapabilityItem] = {}
        self._initialize_default_capabilities()

    def _initialize_default_capabilities(self):
        defaults = [
            ("local_model", CapabilityStatus.UNAVAILABLE, "No local GGUF model binary loaded"),
            ("microphone", CapabilityStatus.UNAVAILABLE, "No microphone audio device detected"),
            ("tts", CapabilityStatus.UNAVAILABLE, "Text-to-speech engine uninitialized"),
            ("wakeword", CapabilityStatus.UNAVAILABLE, "Wake-word engine uninitialized"),
            ("browser", CapabilityStatus.AVAILABLE, "Browser automation framework available"),
            ("playwright", CapabilityStatus.UNAVAILABLE, "Playwright driver uninitialized"),
            ("ocr", CapabilityStatus.UNAVAILABLE, "OCR engine unavailable"),
            ("vision", CapabilityStatus.UNAVAILABLE, "Vision processing model unavailable"),
            ("scheduler", CapabilityStatus.AVAILABLE, "Task scheduler service active"),
            ("desktop_notifications", CapabilityStatus.AVAILABLE, "Desktop notification framework active"),
            ("filesystem", CapabilityStatus.AVAILABLE, "Filesystem sandbox active"),
            ("shell", CapabilityStatus.AVAILABLE, "Controlled shell executor active"),
            ("skills", CapabilityStatus.AVAILABLE, "Skill resolution system ready"),
            ("memory", CapabilityStatus.AVAILABLE, "SQLite persistent memory active"),
        ]
        for name, status, reason in defaults:
            self.register(name, status, reason)

    def register(self, name: str, status: CapabilityStatus, reason: str = "", details: Optional[Dict[str, Any]] = None) -> None:
        item = CapabilityItem(
            name=name,
            status=status,
            reason=reason,
            details=details or {}
        )
        self._capabilities[name] = item

    def get_capability(self, name: str) -> Optional[CapabilityItem]:
        return self._capabilities.get(name)

    def is_available(self, name: str) -> bool:
        cap = self._capabilities.get(name)
        return cap is not None and cap.status == CapabilityStatus.AVAILABLE

    def get_all_capabilities(self) -> Dict[str, CapabilityItem]:
        return dict(self._capabilities)

    def get_status_report(self) -> Dict[str, Any]:
        """Returns structured status report for system.status tool or CLI diagnostics."""
        summary = {
            "total_capabilities": len(self._capabilities),
            "available_count": sum(1 for c in self._capabilities.values() if c.status == CapabilityStatus.AVAILABLE),
            "degraded_count": sum(1 for c in self._capabilities.values() if c.status == CapabilityStatus.DEGRADED),
            "unavailable_count": sum(1 for c in self._capabilities.values() if c.status == CapabilityStatus.UNAVAILABLE),
            "capabilities": {
                name: {"status": c.status.value, "reason": c.reason, "details": c.details}
                for name, c in self._capabilities.items()
            }
        }
        return summary
