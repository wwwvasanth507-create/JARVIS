"""
Single Instance Protection Lock for JARVIS Desktop Application.

Prevents multiple concurrent JARVIS process runtimes using Windows Named Mutex
or fallback socket port lock.
"""

import sys
import ctypes
import logging
import platform
from typing import Optional

logger = logging.getLogger(__name__)

MUTEX_NAME = "JARVIS_DESKTOP_SINGLE_INSTANCE_MUTEX"


class SingleInstanceLock:
    """Manages single-instance mutex lock for desktop application."""

    def __init__(self, mutex_name: str = MUTEX_NAME):
        self.mutex_name = mutex_name
        self._handle: Optional[int] = None
        self._acquired = False

    def acquire(self) -> bool:
        """
        Attempts to acquire single instance lock.
        Returns True if acquired (this process is the sole instance),
        False if another instance is already running.
        """
        if self._acquired:
            return True

        if platform.system().lower() == "windows":
            try:
                # CreateMutexW returns a handle and GetLastError() will be ERROR_ALREADY_EXISTS (183) if it exists
                ERROR_ALREADY_EXISTS = 183
                kernel32 = ctypes.windll.kernel32
                handle = kernel32.CreateMutexW(None, False, self.mutex_name)
                last_error = kernel32.GetLastError()

                if last_error == ERROR_ALREADY_EXISTS:
                    logger.warning(f"Another instance of JARVIS is already running (Mutex {self.mutex_name} exists).")
                    if handle:
                        kernel32.CloseHandle(handle)
                    return False

                self._handle = handle
                self._acquired = True
                logger.info("SingleInstanceLock acquired successfully (Windows Mutex).")
                return True
            except Exception as e:
                logger.warning(f"Could not create Windows Mutex lock: {e}")

        # Fallback cross-platform socket lock
        try:
            import socket
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # Bind to arbitrary specific loopback port
            self._socket.bind(("127.0.0.1", 47823))
            self._acquired = True
            logger.info("SingleInstanceLock acquired successfully (Socket Lock).")
            return True
        except Exception:
            logger.warning("Another instance of JARVIS is already running on port 47823.")
            return False

    def release(self) -> None:
        """Releases the instance mutex handle."""
        if not self._acquired:
            return

        if platform.system().lower() == "windows" and self._handle:
            try:
                ctypes.windll.kernel32.CloseHandle(self._handle)
                self._handle = None
            except Exception as e:
                logger.warning(f"Error closing mutex handle: {e}")

        if hasattr(self, "_socket") and self._socket:
            try:
                self._socket.close()
                self._socket = None
            except Exception:
                pass

        self._acquired = False
        logger.info("SingleInstanceLock released.")
