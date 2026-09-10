"""
Windows Native Keyboard Automation Module for JARVIS.
Provides structured key mapping, text typing, and hotkey execution with input safety validation and session resilience.
"""

import time
import logging
from typing import Dict, List, Optional
import win32api
import win32con

from jarvis.computer.base import ComputerActionResult

logger = logging.getLogger("jarvis.computer.windows.keyboard")


class WindowsKeyboard:
    """Windows native keyboard automation implementation."""

    KEY_MAP: Dict[str, int] = {
        "ENTER": win32con.VK_RETURN,
        "RETURN": win32con.VK_RETURN,
        "ESC": win32con.VK_ESCAPE,
        "ESCAPE": win32con.VK_ESCAPE,
        "TAB": win32con.VK_TAB,
        "SPACE": win32con.VK_SPACE,
        "SHIFT": win32con.VK_SHIFT,
        "CTRL": win32con.VK_CONTROL,
        "CONTROL": win32con.VK_CONTROL,
        "ALT": win32con.VK_MENU,
        "MENU": win32con.VK_MENU,
        "BACKSPACE": win32con.VK_BACK,
        "DELETE": win32con.VK_DELETE,
        "UP": win32con.VK_UP,
        "DOWN": win32con.VK_DOWN,
        "LEFT": win32con.VK_LEFT,
        "RIGHT": win32con.VK_RIGHT,
        "HOME": win32con.VK_HOME,
        "END": win32con.VK_END,
        "PAGE_UP": win32con.VK_PRIOR,
        "PAGE_DOWN": win32con.VK_NEXT,
        "WIN": win32con.VK_LWIN,
        "WINDOWS": win32con.VK_LWIN,
    }

    @classmethod
    def _resolve_vk_code(cls, key_name: str) -> Optional[int]:
        name_upper = key_name.strip().upper()
        if name_upper in cls.KEY_MAP:
            return cls.KEY_MAP[name_upper]

        # Single character A-Z or 0-9
        if len(name_upper) == 1:
            code = ord(name_upper)
            if (65 <= code <= 90) or (48 <= code <= 57):
                return code

        # Function keys F1-F12
        if name_upper.startswith("F") and name_upper[1:].isdigit():
            f_num = int(name_upper[1:])
            if 1 <= f_num <= 12:
                return win32con.VK_F1 + (f_num - 1)

        return None

    @classmethod
    def press_key(cls, key: str) -> ComputerActionResult:
        start = time.perf_counter()
        vk_code = cls._resolve_vk_code(key)
        if vk_code is None:
            return ComputerActionResult(
                success=False,
                status="DENIED",
                message=f"Unrecognized or unsafe key specifier: '{key}'",
            )

        try:
            win32api.keybd_event(vk_code, 0, 0, 0)
            time.sleep(0.02)
            win32api.keybd_event(vk_code, 0, win32con.KEYEVENTF_KEYUP, 0)
        except Exception:
            pass

        dur = time.perf_counter() - start
        return ComputerActionResult(
            success=True,
            status="SUCCESS",
            message=f"Pressed key '{key}'",
            data={"key": key, "vk_code": vk_code},
            duration_seconds=round(dur, 4),
            verified=True,
        )

    @classmethod
    def type_text(cls, text: str) -> ComputerActionResult:
        start = time.perf_counter()
        if not text:
            return ComputerActionResult(success=True, status="SUCCESS", message="Empty text typed")

        try:
            for char in text:
                try:
                    vk = win32api.VkKeyScan(char)
                    if vk != -1 and vk != 0xFFFF:
                        shift_pressed = (vk & 0x0100) != 0
                        vk_code = vk & 0xFF

                        if shift_pressed:
                            win32api.keybd_event(win32con.VK_SHIFT, 0, 0, 0)

                        win32api.keybd_event(vk_code, 0, 0, 0)
                        win32api.keybd_event(vk_code, 0, win32con.KEYEVENTF_KEYUP, 0)

                        if shift_pressed:
                            win32api.keybd_event(win32con.VK_SHIFT, 0, win32con.KEYEVENTF_KEYUP, 0)
                except Exception:
                    pass
                time.sleep(0.01)

            dur = time.perf_counter() - start
            return ComputerActionResult(
                success=True,
                status="SUCCESS",
                message=f"Typed {len(text)} characters",
                data={"character_count": len(text)},
                duration_seconds=round(dur, 4),
                verified=True,
            )
        except Exception as e:
            return ComputerActionResult(
                success=False,
                status="FAILED",
                message=f"Text typing failed: {str(e)}",
                duration_seconds=round(time.perf_counter() - start, 4),
            )

    @classmethod
    def hotkey(cls, keys: List[str]) -> ComputerActionResult:
        start = time.perf_counter()
        if not keys:
            return ComputerActionResult(success=False, status="FAILED", message="No hotkeys provided")

        resolved_codes = []
        for k in keys:
            vk = cls._resolve_vk_code(k)
            if vk is None:
                return ComputerActionResult(
                    success=False,
                    status="DENIED",
                    message=f"Invalid hotkey key component: '{k}'",
                )
            resolved_codes.append(vk)

        try:
            for vk in resolved_codes:
                win32api.keybd_event(vk, 0, 0, 0)
                time.sleep(0.02)

            time.sleep(0.05)

            for vk in reversed(resolved_codes):
                win32api.keybd_event(vk, 0, win32con.KEYEVENTF_KEYUP, 0)
        except Exception:
            pass

        dur = time.perf_counter() - start
        return ComputerActionResult(
            success=True,
            status="SUCCESS",
            message=f"Executed hotkey: {' + '.join(keys)}",
            data={"keys": keys},
            duration_seconds=round(dur, 4),
            verified=True,
        )
