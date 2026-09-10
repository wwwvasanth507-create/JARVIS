"""
User-Controlled Desktop Autostart Configuration for JARVIS (Windows-friendly).

Provides explicit, reversible autostart setup via Windows Registry (HKCU).
Disabled by default unless requested by the user.
"""

import sys
import logging
import platform

logger = logging.getLogger(__name__)

REG_KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "JARVIS_Desktop_Assistant"


class AutostartManager:
    """Manages explicit user-controlled desktop autostart registration."""

    @classmethod
    def is_supported(cls) -> bool:
        return platform.system().lower() == "windows"

    @classmethod
    def is_enabled(cls) -> bool:
        if not cls.is_supported():
            return False

        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_KEY_PATH, 0, winreg.KEY_READ) as key:
                val, _ = winreg.QueryValueEx(key, APP_NAME)
                return bool(val)
        except Exception:
            return False

    @classmethod
    def enable_autostart(cls, executable_path: str = sys.executable) -> bool:
        if not cls.is_supported():
            logger.warning("Autostart configuration is only supported on Windows.")
            return False

        cmd = f'"{executable_path}" -m jarvis'
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_KEY_PATH, 0, winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, cmd)
            logger.info(f"Autostart enabled for JARVIS: {cmd}")
            return True
        except Exception as e:
            logger.error(f"Failed to enable autostart: {e}")
            return False

    @classmethod
    def disable_autostart(cls) -> bool:
        if not cls.is_supported():
            return False

        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_KEY_PATH, 0, winreg.KEY_SET_VALUE) as key:
                try:
                    winreg.DeleteValue(key, APP_NAME)
                    logger.info("Autostart disabled for JARVIS.")
                except FileNotFoundError:
                    pass
            return True
        except Exception as e:
            logger.error(f"Failed to disable autostart: {e}")
            return False
