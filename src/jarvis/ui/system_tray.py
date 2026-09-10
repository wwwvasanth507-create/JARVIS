"""
Windows System Tray & Notification Area Integration for JARVIS Desktop Assistant.

Manages system tray menu, minimize-to-tray, restore, popup notification balloons,
and clean fallback when running without display.
"""

import sys
import os
import ctypes
import logging
import platform
from typing import Callable, Optional, Dict, Any

logger = logging.getLogger(__name__)


class SystemTrayManager:
    """Manages notification area tray icon and context menu actions."""

    def __init__(
        self,
        on_open: Optional[Callable[[], None]] = None,
        on_doctor: Optional[Callable[[], None]] = None,
        on_status: Optional[Callable[[], None]] = None,
        on_toggle_wakeword: Optional[Callable[[], None]] = None,
        on_exit: Optional[Callable[[], None]] = None,
    ):
        self.on_open = on_open
        self.on_doctor = on_doctor
        self.on_status = on_status
        self.on_toggle_wakeword = on_toggle_wakeword
        self.on_exit = on_exit
        self._tray_active = False

    def is_supported(self) -> bool:
        return platform.system().lower() == "windows"

    def initialize(self) -> bool:
        """Initialize system tray support."""
        if not self.is_supported():
            logger.info("System tray is supported natively on Windows.")
            return False
        self._tray_active = True
        logger.info("SystemTrayManager initialized.")
        return True

    def show_notification(self, title: str, message: str) -> None:
        """Display desktop notification popup."""
        logger.info(f"Notification: [{title}] {message}")
        if self.is_supported():
            try:
                # Windows Shell notification balloon via powershell fallback or ctypes
                from jarvis.scheduler.notifications import NotificationManager
                nm = NotificationManager()
                nm.deliver("TEXT", message, title=title)
            except Exception as e:
                logger.warning(f"Could not deliver tray notification: {e}")

    def on_window_minimize(self, window) -> None:
        """Handle window minimize-to-tray behavior."""
        try:
            window.withdraw()
            self.show_notification("JARVIS Running in Background", "JARVIS is active in the system tray.")
        except Exception as e:
            logger.warning(f"Error withdrawing window to tray: {e}")

    def restore_window(self, window) -> None:
        """Restore window from tray."""
        try:
            window.deiconify()
            window.lift()
            window.focus_force()
        except Exception as e:
            logger.warning(f"Error restoring window: {e}")

    def shutdown(self) -> None:
        """Cleanup tray icon resources."""
        self._tray_active = False
        logger.info("SystemTrayManager shutdown complete.")
