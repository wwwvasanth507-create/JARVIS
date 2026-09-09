"""
Audio Resource Ownership Lock Manager for JARVIS.
Prevents concurrent components (WakeWord, STT, Push-to-Talk) from colliding on microphone access.
"""

import threading
import time
import logging
from typing import Optional

logger = logging.getLogger("jarvis.voice.ownership")


class AudioOwnershipManager:
    """
    Manages exclusive ownership of audio input hardware.
    """

    def __init__(self, default_timeout_seconds: float = 5.0):
        self.default_timeout = default_timeout_seconds
        self._lock = threading.Lock()
        self._current_owner: str = "none"
        self._acquired_at: float = 0.0

    @property
    def current_owner(self) -> str:
        with self._lock:
            # Check for stale ownership timeout
            if self._current_owner != "none" and (time.time() - self._acquired_at > self.default_timeout):
                logger.warning(f"Audio ownership lock held by '{self._current_owner}' timed out. Resetting.")
                self._current_owner = "none"
            return self._current_owner

    def acquire(self, owner: str, timeout_seconds: Optional[float] = None) -> bool:
        """Acquires microphone ownership lock for a specified owner."""
        timeout = timeout_seconds or self.default_timeout
        start_time = time.time()

        while time.time() - start_time < timeout:
            with self._lock:
                if self._current_owner in ("none", owner):
                    self._current_owner = owner
                    self._acquired_at = time.time()
                    logger.debug(f"Audio ownership acquired by '{owner}'")
                    return True
            time.sleep(0.02)

        logger.warning(f"Failed to acquire audio ownership for '{owner}'. Current owner: '{self._current_owner}'")
        return False

    def release(self, owner: str) -> None:
        """Releases microphone ownership lock if currently held by owner."""
        with self._lock:
            if self._current_owner == owner:
                self._current_owner = "none"
                self._acquired_at = 0.0
                logger.debug(f"Audio ownership released by '{owner}'")
