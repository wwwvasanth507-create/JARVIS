"""
Wake-Word Detector Interface Abstraction for JARVIS.
Prepared for continuous wake-word listening in PROMPT 004.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import logging

logger = logging.getLogger("jarvis.voice.wakeword")


class WakeWordDetector(ABC):
    """Abstract Base Class for Wake-Word Detectors."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.wake_word = self.config.get("wake_word", "JARVIS")
        self.is_active = False

    @abstractmethod
    def is_detected(self, audio_chunk: bytes) -> bool:
        """Returns True if the wake-word was detected in the audio chunk."""
        pass

    @abstractmethod
    def start(self) -> None:
        """Starts background wake-word detector."""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stops background wake-word detector."""
        pass


class MockWakeWordDetector(WakeWordDetector):
    """Mock Wake-Word Detector for testing and placeholder readiness."""

    def is_detected(self, audio_chunk: bytes) -> bool:
        # Not active in PROMPT 003
        return False

    def start(self) -> None:
        self.is_active = True
        logger.info(f"WakeWordDetector interface prepared for keyword '{self.wake_word}' (Disabled for PROMPT 003)")

    def stop(self) -> None:
        self.is_active = False
