"""
Windows Master ComputerController Implementation for JARVIS.
Integrates WindowsMouse, WindowsKeyboard, WindowsScreen, and WindowsWindowManager.
"""

from typing import List, Optional, Tuple
import time

from jarvis.computer.base import (
    ComputerActionResult,
    ComputerController,
    ComputerState,
    CursorPosition,
    ScreenSize,
    WindowInfo,
)
from jarvis.computer.windows.mouse import WindowsMouse
from jarvis.computer.windows.keyboard import WindowsKeyboard
from jarvis.computer.windows.screen import WindowsScreen
from jarvis.computer.windows.window import WindowsWindowManager


class WindowsComputerController(ComputerController):
    """Windows native master ComputerController."""

    def get_state(self) -> ComputerState:
        active_win = WindowsWindowManager.get_active_window()
        cursor_pos = WindowsMouse.get_position()
        screen_size = WindowsScreen.get_screen_size()
        return ComputerState(
            active_window=active_win,
            cursor_position=cursor_pos,
            screen_size=screen_size,
            timestamp=time.time(),
        )

    def move_mouse(self, x: int, y: int) -> ComputerActionResult:
        return WindowsMouse.move(x, y)

    def click(self, x: Optional[int] = None, y: Optional[int] = None, button: str = "left") -> ComputerActionResult:
        return WindowsMouse.click(x=x, y=y, button=button)

    def double_click(self, x: Optional[int] = None, y: Optional[int] = None) -> ComputerActionResult:
        return WindowsMouse.double_click(x=x, y=y)

    def right_click(self, x: Optional[int] = None, y: Optional[int] = None) -> ComputerActionResult:
        return WindowsMouse.click(x=x, y=y, button="right")

    def mouse_down(self, button: str = "left") -> ComputerActionResult:
        return WindowsMouse.mouse_down(button=button)

    def mouse_up(self, button: str = "left") -> ComputerActionResult:
        return WindowsMouse.mouse_up(button=button)

    def scroll(self, clicks: int = 3, direction: str = "down") -> ComputerActionResult:
        return WindowsMouse.scroll(clicks=clicks, direction=direction)

    def type_text(self, text: str) -> ComputerActionResult:
        return WindowsKeyboard.type_text(text)

    def press_key(self, key: str) -> ComputerActionResult:
        return WindowsKeyboard.press_key(key)

    def hotkey(self, keys: List[str]) -> ComputerActionResult:
        return WindowsKeyboard.hotkey(keys)

    def screenshot(
        self, region: Optional[Tuple[int, int, int, int]] = None, active_window_only: bool = False
    ) -> ComputerActionResult:
        return WindowsScreen.screenshot(region=region, active_window_only=active_window_only)

    def list_windows(self) -> List[WindowInfo]:
        return WindowsWindowManager.list_windows()

    def get_active_window(self) -> Optional[WindowInfo]:
        return WindowsWindowManager.get_active_window()

    def focus_window(self, title_or_hwnd: str | int) -> ComputerActionResult:
        return WindowsWindowManager.focus_window(title_or_hwnd)

    def minimize_window(self, title_or_hwnd: str | int) -> ComputerActionResult:
        return WindowsWindowManager.minimize_window(title_or_hwnd)

    def maximize_window(self, title_or_hwnd: str | int) -> ComputerActionResult:
        return WindowsWindowManager.maximize_window(title_or_hwnd)

    def restore_window(self, title_or_hwnd: str | int) -> ComputerActionResult:
        return WindowsWindowManager.restore_window(title_or_hwnd)

    def close_window(self, title_or_hwnd: str | int) -> ComputerActionResult:
        return WindowsWindowManager.close_window(title_or_hwnd)
