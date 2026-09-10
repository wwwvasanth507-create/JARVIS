"""
Base Interfaces, Data Models, and Abstract ComputerController for JARVIS.
Provides platform-agnostic contracts for mouse, keyboard, screen, window, and process control.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple
import time
from pydantic import BaseModel, Field


class CursorPosition(BaseModel):
    x: int = 0
    y: int = 0


class ScreenSize(BaseModel):
    width: int = 1920
    height: int = 1080


class WindowInfo(BaseModel):
    hwnd: int = 0
    title: str = ""
    process_id: int = 0
    process_name: str = ""
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0
    is_active: bool = False
    is_minimized: bool = False
    is_maximized: bool = False


class ComputerState(BaseModel):
    active_window: Optional[WindowInfo] = None
    cursor_position: CursorPosition = Field(default_factory=CursorPosition)
    screen_size: ScreenSize = Field(default_factory=ScreenSize)
    timestamp: float = Field(default_factory=time.time)


class ComputerActionResult(BaseModel):
    success: bool
    status: str = "SUCCESS"  # SUCCESS, FAILED, TIMEOUT, DENIED, UNCERTAIN
    message: str = ""
    data: Optional[Any] = None
    duration_seconds: float = 0.0
    verified: bool = False


class ComputerController(ABC):
    """Abstract Base Class for Platform-Specific Computer Controllers."""

    @abstractmethod
    def get_state(self) -> ComputerState:
        """Retrieves lightweight current computer state."""
        pass

    @abstractmethod
    def move_mouse(self, x: int, y: int) -> ComputerActionResult:
        """Moves cursor to (x, y) coordinates."""
        pass

    @abstractmethod
    def click(self, x: Optional[int] = None, y: Optional[int] = None, button: str = "left") -> ComputerActionResult:
        """Performs mouse click."""
        pass

    @abstractmethod
    def double_click(self, x: Optional[int] = None, y: Optional[int] = None) -> ComputerActionResult:
        """Performs mouse double click."""
        pass

    @abstractmethod
    def right_click(self, x: Optional[int] = None, y: Optional[int] = None) -> ComputerActionResult:
        """Performs mouse right click."""
        pass

    @abstractmethod
    def mouse_down(self, button: str = "left") -> ComputerActionResult:
        """Presses mouse button down."""
        pass

    @abstractmethod
    def mouse_up(self, button: str = "left") -> ComputerActionResult:
        """Releases mouse button up."""
        pass

    @abstractmethod
    def scroll(self, clicks: int = 3, direction: str = "down") -> ComputerActionResult:
        """Scrolls mouse wheel."""
        pass

    @abstractmethod
    def type_text(self, text: str) -> ComputerActionResult:
        """Types structured text string."""
        pass

    @abstractmethod
    def press_key(self, key: str) -> ComputerActionResult:
        """Presses single key."""
        pass

    @abstractmethod
    def hotkey(self, keys: List[str]) -> ComputerActionResult:
        """Executes hotkey key sequence (e.g. ['ctrl', 'c'])."""
        pass

    @abstractmethod
    def screenshot(
        self, region: Optional[Tuple[int, int, int, int]] = None, active_window_only: bool = False
    ) -> ComputerActionResult:
        """Captures screenshot."""
        pass

    @abstractmethod
    def list_windows(self) -> List[WindowInfo]:
        """Lists active top-level windows."""
        pass

    @abstractmethod
    def get_active_window(self) -> Optional[WindowInfo]:
        """Returns active foreground window."""
        pass

    @abstractmethod
    def focus_window(self, title_or_hwnd: str | int) -> ComputerActionResult:
        """Brings window to foreground focus."""
        pass

    @abstractmethod
    def minimize_window(self, title_or_hwnd: str | int) -> ComputerActionResult:
        """Minimizes window."""
        pass

    @abstractmethod
    def maximize_window(self, title_or_hwnd: str | int) -> ComputerActionResult:
        """Maximizes window."""
        pass

    @abstractmethod
    def restore_window(self, title_or_hwnd: str | int) -> ComputerActionResult:
        """Restores window."""
        pass

    @abstractmethod
    def close_window(self, title_or_hwnd: str | int) -> ComputerActionResult:
        """Requests graceful window closure."""
        pass
