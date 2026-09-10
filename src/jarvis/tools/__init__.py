"""
JARVIS Tool Subsystem and Registry.
"""

from jarvis.tools.base import BaseTool, ToolMetadata, ToolResult
from jarvis.tools.computer_tools import (
    MoveMouseTool,
    ClickTool,
    DoubleClickTool,
    RightClickTool,
    ScrollTool,
    TypeTool,
    PressKeyTool,
    HotkeyTool,
    ScreenshotTool,
    ActiveWindowTool,
    ListWindowsTool,
    FocusWindowTool,
    CloseWindowTool,
)
from jarvis.tools.application_tools import (
    ListApplicationsTool,
    OpenApplicationTool,
    CloseApplicationTool,
    IsApplicationRunningTool,
)
from jarvis.tools.browser_tools import BROWSER_TOOLS

ALL_TOOLS = [
    MoveMouseTool(),
    ClickTool(),
    DoubleClickTool(),
    RightClickTool(),
    ScrollTool(),
    TypeTool(),
    PressKeyTool(),
    HotkeyTool(),
    ScreenshotTool(),
    ActiveWindowTool(),
    ListWindowsTool(),
    FocusWindowTool(),
    CloseWindowTool(),
    ListApplicationsTool(),
    OpenApplicationTool(),
    CloseApplicationTool(),
    IsApplicationRunningTool(),
    *BROWSER_TOOLS,
]

__all__ = [
    "BaseTool",
    "ToolMetadata",
    "ToolResult",
    "ALL_TOOLS",
    "BROWSER_TOOLS",
    "MoveMouseTool",
    "ClickTool",
    "DoubleClickTool",
    "RightClickTool",
    "ScrollTool",
    "TypeTool",
    "PressKeyTool",
    "HotkeyTool",
    "ScreenshotTool",
    "ActiveWindowTool",
    "ListWindowsTool",
    "FocusWindowTool",
    "CloseWindowTool",
    "ListApplicationsTool",
    "OpenApplicationTool",
    "CloseApplicationTool",
    "IsApplicationRunningTool",
]

