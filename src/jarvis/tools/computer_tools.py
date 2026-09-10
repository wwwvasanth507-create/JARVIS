"""
Structured Computer Control Tools for JARVIS.
Exposes mouse, keyboard, screenshot, and window management tools with permission evaluation.
"""

from typing import Any, Dict, List, Optional
from jarvis.tools.base import BaseTool, ToolMetadata, ToolResult
from jarvis.security.permissions import PermissionCategory, RiskLevel, PermissionEvaluator
from jarvis.computer.factory import ComputerControllerFactory
from jarvis.computer.base import ComputerController

# Global controller instance
controller: ComputerController = ComputerControllerFactory.get_controller()
evaluator = PermissionEvaluator()


class ComputerBaseTool(BaseTool):
    """Base class for Computer tools enforcing permission security checks."""

    def __init__(self, name: str, description: str, category: PermissionCategory, risk: RiskLevel, schema: Dict[str, Any]):
        meta = ToolMetadata(
            name=name,
            description=description,
            input_schema=schema,
            permission_requirement=category,
            risk_level=risk,
            verification_strategy="state_check",
        )
        super().__init__(meta)

    def _check_permission(self, action_name: str, kwargs: Dict[str, Any]) -> ToolResult | None:
        chk = evaluator.evaluate(
            category=self.metadata.permission_requirement,
            risk_level=self.metadata.risk_level,
            action_name=action_name,
            parameters=kwargs,
        )
        if not chk.allowed:
            return ToolResult(success=False, error=f"Permission Denied [{action_name}]: {chk.reason}")
        return None


class MoveMouseTool(ComputerBaseTool):
    def __init__(self):
        super().__init__(
            name="computer.move_mouse",
            description="Moves the mouse cursor to target (x, y) coordinates.",
            category=PermissionCategory.COMPUTER_CONTROL,
            risk=RiskLevel.LOW,
            schema={
                "type": "object",
                "properties": {"x": {"type": "integer"}, "y": {"type": "integer"}},
                "required": ["x", "y"],
            },
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        perm_err = self._check_permission(self.name, kwargs)
        if perm_err:
            return perm_err

        res = controller.move_mouse(kwargs["x"], kwargs["y"])
        return ToolResult(
            success=res.success,
            data=res.data,
            error=None if res.success else res.message,
            verification_details={"verified": res.verified, "status": res.status},
        )

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return bool(execution_result.verification_details and execution_result.verification_details.get("verified"))


class ClickTool(ComputerBaseTool):
    def __init__(self):
        super().__init__(
            name="computer.click",
            description="Performs a mouse click at optional (x, y) coordinates.",
            category=PermissionCategory.COMPUTER_CONTROL,
            risk=RiskLevel.LOW,
            schema={
                "type": "object",
                "properties": {
                    "x": {"type": "integer"},
                    "y": {"type": "integer"},
                    "button": {"type": "string", "enum": ["left", "right", "middle"], "default": "left"},
                },
            },
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        perm_err = self._check_permission(self.name, kwargs)
        if perm_err:
            return perm_err

        res = controller.click(x=kwargs.get("x"), y=kwargs.get("y"), button=kwargs.get("button", "left"))
        return ToolResult(
            success=res.success,
            data=res.data,
            error=None if res.success else res.message,
            verification_details={"verified": res.verified, "status": res.status},
        )

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class DoubleClickTool(ComputerBaseTool):
    def __init__(self):
        super().__init__(
            name="computer.double_click",
            description="Performs a mouse double click at optional (x, y) coordinates.",
            category=PermissionCategory.COMPUTER_CONTROL,
            risk=RiskLevel.LOW,
            schema={
                "type": "object",
                "properties": {"x": {"type": "integer"}, "y": {"type": "integer"}},
            },
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        perm_err = self._check_permission(self.name, kwargs)
        if perm_err:
            return perm_err

        res = controller.double_click(x=kwargs.get("x"), y=kwargs.get("y"))
        return ToolResult(
            success=res.success,
            data=res.data,
            error=None if res.success else res.message,
            verification_details={"verified": res.verified, "status": res.status},
        )

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class RightClickTool(ComputerBaseTool):
    def __init__(self):
        super().__init__(
            name="computer.right_click",
            description="Performs a mouse right click at optional (x, y) coordinates.",
            category=PermissionCategory.COMPUTER_CONTROL,
            risk=RiskLevel.LOW,
            schema={
                "type": "object",
                "properties": {"x": {"type": "integer"}, "y": {"type": "integer"}},
            },
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        perm_err = self._check_permission(self.name, kwargs)
        if perm_err:
            return perm_err

        res = controller.right_click(x=kwargs.get("x"), y=kwargs.get("y"))
        return ToolResult(
            success=res.success,
            data=res.data,
            error=None if res.success else res.message,
            verification_details={"verified": res.verified, "status": res.status},
        )

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class ScrollTool(ComputerBaseTool):
    def __init__(self):
        super().__init__(
            name="computer.scroll",
            description="Scrolls mouse wheel up or down.",
            category=PermissionCategory.COMPUTER_CONTROL,
            risk=RiskLevel.LOW,
            schema={
                "type": "object",
                "properties": {
                    "clicks": {"type": "integer", "default": 3},
                    "direction": {"type": "string", "enum": ["up", "down"], "default": "down"},
                },
            },
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        perm_err = self._check_permission(self.name, kwargs)
        if perm_err:
            return perm_err

        res = controller.scroll(clicks=kwargs.get("clicks", 3), direction=kwargs.get("direction", "down"))
        return ToolResult(
            success=res.success,
            data=res.data,
            error=None if res.success else res.message,
            verification_details={"verified": res.verified, "status": res.status},
        )

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class TypeTool(ComputerBaseTool):
    def __init__(self):
        super().__init__(
            name="computer.type",
            description="Types structured text via keyboard simulation.",
            category=PermissionCategory.COMPUTER_CONTROL,
            risk=RiskLevel.MEDIUM,
            schema={
                "type": "object",
                "properties": {"text": {"type": "string"}},
                "required": ["text"],
            },
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        perm_err = self._check_permission(self.name, kwargs)
        if perm_err:
            return perm_err

        res = controller.type_text(kwargs["text"])
        return ToolResult(
            success=res.success,
            data=res.data,
            error=None if res.success else res.message,
            verification_details={"verified": res.verified, "status": res.status},
        )

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class PressKeyTool(ComputerBaseTool):
    def __init__(self):
        super().__init__(
            name="computer.press",
            description="Presses a single keyboard key (e.g. ENTER, ESC, TAB, SHIFT, CTRL).",
            category=PermissionCategory.COMPUTER_CONTROL,
            risk=RiskLevel.LOW,
            schema={
                "type": "object",
                "properties": {"key": {"type": "string"}},
                "required": ["key"],
            },
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        perm_err = self._check_permission(self.name, kwargs)
        if perm_err:
            return perm_err

        res = controller.press_key(kwargs["key"])
        return ToolResult(
            success=res.success,
            data=res.data,
            error=None if res.success else res.message,
            verification_details={"verified": res.verified, "status": res.status},
        )

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class HotkeyTool(ComputerBaseTool):
    def __init__(self):
        super().__init__(
            name="computer.hotkey",
            description="Executes a key shortcut sequence (e.g. ['CTRL', 'C']).",
            category=PermissionCategory.COMPUTER_CONTROL,
            risk=RiskLevel.MEDIUM,
            schema={
                "type": "object",
                "properties": {
                    "keys": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["keys"],
            },
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        perm_err = self._check_permission(self.name, kwargs)
        if perm_err:
            return perm_err

        res = controller.hotkey(kwargs["keys"])
        return ToolResult(
            success=res.success,
            data=res.data,
            error=None if res.success else res.message,
            verification_details={"verified": res.verified, "status": res.status},
        )

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class ScreenshotTool(ComputerBaseTool):
    def __init__(self):
        super().__init__(
            name="computer.screenshot",
            description="Captures a desktop screenshot of full screen, region, or active window.",
            category=PermissionCategory.SCREEN_READ,
            risk=RiskLevel.LOW,
            schema={
                "type": "object",
                "properties": {
                    "active_window_only": {"type": "boolean", "default": False},
                },
            },
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        perm_err = self._check_permission(self.name, kwargs)
        if perm_err:
            return perm_err

        res = controller.screenshot(active_window_only=kwargs.get("active_window_only", False))
        return ToolResult(
            success=res.success,
            data=res.data,
            error=None if res.success else res.message,
            verification_details={"verified": res.verified, "status": res.status},
        )

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class ActiveWindowTool(ComputerBaseTool):
    def __init__(self):
        super().__init__(
            name="computer.active_window",
            description="Retrieves metadata for the active foreground window.",
            category=PermissionCategory.SCREEN_READ,
            risk=RiskLevel.LOW,
            schema={"type": "object", "properties": {}},
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        perm_err = self._check_permission(self.name, kwargs)
        if perm_err:
            return perm_err

        active_win = controller.get_active_window()
        return ToolResult(
            success=active_win is not None,
            data=active_win.model_dump() if active_win else None,
            error=None if active_win else "No active window found",
            verification_details={"verified": active_win is not None},
        )

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class ListWindowsTool(ComputerBaseTool):
    def __init__(self):
        super().__init__(
            name="computer.list_windows",
            description="Lists all visible top-level desktop windows.",
            category=PermissionCategory.SCREEN_READ,
            risk=RiskLevel.LOW,
            schema={"type": "object", "properties": {}},
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        perm_err = self._check_permission(self.name, kwargs)
        if perm_err:
            return perm_err

        windows = controller.list_windows()
        return ToolResult(
            success=True,
            data=[w.model_dump() for w in windows],
            error=None,
            verification_details={"verified": True, "count": len(windows)},
        )

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return True


class FocusWindowTool(ComputerBaseTool):
    def __init__(self):
        super().__init__(
            name="computer.focus_window",
            description="Brings a window matching title or process name to foreground focus.",
            category=PermissionCategory.COMPUTER_CONTROL,
            risk=RiskLevel.LOW,
            schema={
                "type": "object",
                "properties": {"title_or_hwnd": {"type": "string"}},
                "required": ["title_or_hwnd"],
            },
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        perm_err = self._check_permission(self.name, kwargs)
        if perm_err:
            return perm_err

        res = controller.focus_window(kwargs["title_or_hwnd"])
        return ToolResult(
            success=res.success,
            data=res.data,
            error=None if res.success else res.message,
            verification_details={"verified": res.verified, "status": res.status},
        )

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return bool(execution_result.verification_details and execution_result.verification_details.get("verified"))


class CloseWindowTool(ComputerBaseTool):
    def __init__(self):
        super().__init__(
            name="computer.close_window",
            description="Requests graceful closure of a target window.",
            category=PermissionCategory.APPLICATION_CONTROL,
            risk=RiskLevel.MEDIUM,
            schema={
                "type": "object",
                "properties": {"title_or_hwnd": {"type": "string"}},
                "required": ["title_or_hwnd"],
            },
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        perm_err = self._check_permission(self.name, kwargs)
        if perm_err:
            return perm_err

        res = controller.close_window(kwargs["title_or_hwnd"])
        return ToolResult(
            success=res.success,
            data=res.data,
            error=None if res.success else res.message,
            verification_details={"verified": res.verified, "status": res.status},
        )

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return bool(execution_result.verification_details and execution_result.verification_details.get("verified"))
