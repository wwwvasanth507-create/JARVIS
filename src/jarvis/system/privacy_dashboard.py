"""
Desktop System Privacy Dashboard Manager for JARVIS.

Tracks hardware/capability access (microphone, wake word, screen, browser, filesystem,
background monitors, memory, network) with audit reasons and activity timestamps.
"""

import time
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class PrivacyCapabilityState(BaseModel):
    capability_name: str
    enabled: bool = True
    reason: str
    last_activity: float = Field(default_factory=time.time)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PrivacyDashboardManager:
    """Manages system privacy capability states for user UI visibility."""

    _instance: Optional["PrivacyDashboardManager"] = None

    def __init__(self):
        self._states: Dict[str, PrivacyCapabilityState] = {}
        self._initialize_default_privacy_states()

    @classmethod
    def get_instance(cls) -> "PrivacyDashboardManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def update_capability_state(self, capability_name: str, enabled: bool, reason: str, metadata: Optional[Dict[str, Any]] = None) -> PrivacyCapabilityState:
        state = PrivacyCapabilityState(
            capability_name=capability_name,
            enabled=enabled,
            reason=reason,
            last_activity=time.time(),
            metadata=metadata or {}
        )
        self._states[capability_name] = state
        logger.info(f"PrivacyDashboardManager updated state for '{capability_name}': enabled={enabled} ({reason})")
        return state

    def get_privacy_states(self) -> Dict[str, PrivacyCapabilityState]:
        return self._states

    def _initialize_default_privacy_states(self) -> None:
        defaults = [
            ("microphone", True, "STT and Voice Assistant active"),
            ("wake_word", True, "Background wake word detector listening"),
            ("screen_access", True, "OCR and screen analysis tool available"),
            ("browser_access", True, "Playwright local browser controller active"),
            ("filesystem_access", True, "Filesystem tools bound to workspace root"),
            ("background_monitors", True, "Governed user condition monitors active"),
            ("memory_access", True, "Local SQLite memory database active"),
            ("network_access", True, "Local network diagnostics and web browser search"),
        ]
        for name, enabled, reason in defaults:
            self._states[name] = PrivacyCapabilityState(
                capability_name=name,
                enabled=enabled,
                reason=reason,
                last_activity=time.time()
            )
