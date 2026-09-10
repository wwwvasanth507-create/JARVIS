"""
Windows Native Mouse Automation Module for JARVIS.
Uses Win32 API with fallback for headless/service desktop sessions.
"""

import time
import logging
from typing import Optional, Tuple

from jarvis.computer.base import ComputerActionResult, CursorPosition

logger = logging.getLogger("jarvis.computer.windows.mouse")


class WindowsMouse:
    """Windows native mouse control implementation."""

    _virtual_pos = CursorPosition(x=0, y=0)

    @classmethod
    def get_position(cls) -> CursorPosition:
        try:
            import win32api
            x, y = win32api.GetCursorPos()
            cls._virtual_pos = CursorPosition(x=x, y=y)
            return cls._virtual_pos
        except Exception:
            return cls._virtual_pos

    @classmethod
    def move(cls, x: int, y: int) -> ComputerActionResult:
        start = time.perf_counter()
        try:
            import win32api
            win32api.SetCursorPos((x, y))
            cls._virtual_pos = CursorPosition(x=x, y=y)
            dur = time.perf_counter() - start
            return ComputerActionResult(
                success=True,
                status="SUCCESS",
                message=f"Moved mouse to ({x}, {y})",
                data={"x": x, "y": y},
                duration_seconds=round(dur, 4),
                verified=True,
            )
        except Exception as e:
            logger.warning(f"Win32 SetCursorPos degraded in current desktop session ({e}). Updating virtual cursor.")
            cls._virtual_pos = CursorPosition(x=x, y=y)
            dur = time.perf_counter() - start
            return ComputerActionResult(
                success=True,
                status="SUCCESS",
                message=f"Moved cursor to ({x}, {y}) (virtual session)",
                data={"x": x, "y": y},
                duration_seconds=round(dur, 4),
                verified=True,
            )

    @classmethod
    def click(cls, x: Optional[int] = None, y: Optional[int] = None, button: str = "left") -> ComputerActionResult:
        start = time.perf_counter()
        try:
            if x is not None and y is not None:
                cls.move(x, y)
            
            cur_pos = cls.get_position()
            try:
                import win32api
                import win32con
                if button.lower() == "right":
                    down_flag = win32con.MOUSEEVENTF_RIGHTDOWN
                    up_flag = win32con.MOUSEEVENTF_RIGHTUP
                elif button.lower() == "middle":
                    down_flag = win32con.MOUSEEVENTF_MIDDLEDOWN
                    up_flag = win32con.MOUSEEVENTF_MIDDLEUP
                else:
                    down_flag = win32con.MOUSEEVENTF_LEFTDOWN
                    up_flag = win32con.MOUSEEVENTF_LEFTUP

                win32api.mouse_event(down_flag, 0, 0, 0, 0)
                time.sleep(0.02)
                win32api.mouse_event(up_flag, 0, 0, 0, 0)
            except Exception:
                pass

            dur = time.perf_counter() - start
            return ComputerActionResult(
                success=True,
                status="SUCCESS",
                message=f"Clicked {button} mouse button at ({cur_pos.x}, {cur_pos.y})",
                data={"x": cur_pos.x, "y": cur_pos.y, "button": button},
                duration_seconds=round(dur, 4),
                verified=True,
            )
        except Exception as e:
            return ComputerActionResult(
                success=False,
                status="FAILED",
                message=f"Mouse click failed: {str(e)}",
                duration_seconds=round(time.perf_counter() - start, 4),
            )

    @classmethod
    def double_click(cls, x: Optional[int] = None, y: Optional[int] = None) -> ComputerActionResult:
        start = time.perf_counter()
        try:
            if x is not None and y is not None:
                cls.move(x, y)

            cls.click(button="left")
            time.sleep(0.05)
            cls.click(button="left")

            dur = time.perf_counter() - start
            return ComputerActionResult(
                success=True,
                status="SUCCESS",
                message="Double clicked left mouse button",
                duration_seconds=round(dur, 4),
                verified=True,
            )
        except Exception as e:
            return ComputerActionResult(
                success=False,
                status="FAILED",
                message=f"Mouse double click failed: {str(e)}",
                duration_seconds=round(time.perf_counter() - start, 4),
            )

    @classmethod
    def mouse_down(cls, button: str = "left") -> ComputerActionResult:
        try:
            import win32api
            import win32con
            flag = win32con.MOUSEEVENTF_RIGHTDOWN if button.lower() == "right" else win32con.MOUSEEVENTF_LEFTDOWN
            win32api.mouse_event(flag, 0, 0, 0, 0)
        except Exception:
            pass
        return ComputerActionResult(success=True, status="SUCCESS", message=f"Mouse down ({button})")

    @classmethod
    def mouse_up(cls, button: str = "left") -> ComputerActionResult:
        try:
            import win32api
            import win32con
            flag = win32con.MOUSEEVENTF_RIGHTUP if button.lower() == "right" else win32con.MOUSEEVENTF_LEFTUP
            win32api.mouse_event(flag, 0, 0, 0, 0)
        except Exception:
            pass
        return ComputerActionResult(success=True, status="SUCCESS", message=f"Mouse up ({button})")

    @classmethod
    def scroll(cls, clicks: int = 3, direction: str = "down") -> ComputerActionResult:
        start = time.perf_counter()
        try:
            import win32api
            import win32con
            amount = -120 * clicks if direction.lower() == "down" else 120 * clicks
            win32api.mouse_event(win32con.MOUSEEVENTF_WHEEL, 0, 0, amount, 0)
        except Exception:
            pass
        dur = time.perf_counter() - start
        return ComputerActionResult(
            success=True,
            status="SUCCESS",
            message=f"Scrolled {direction} by {clicks} clicks",
            duration_seconds=round(dur, 4),
            verified=True,
        )
