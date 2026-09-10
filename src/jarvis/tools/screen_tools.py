"""
Structured Screen Understanding, OCR & Vision Tools for JARVIS.
"""

from typing import Any, Dict, Optional
from jarvis.computer.vision.manager import ScreenVisionManager
from jarvis.computer.vision.models import CaptureMode
from jarvis.security.permissions import PermissionCategory, RiskLevel
from jarvis.tools.base import BaseTool, ToolMetadata, ToolResult

_vision_manager = ScreenVisionManager()


class ScreenCaptureTool(BaseTool):
    def __init__(self, manager: Optional[ScreenVisionManager] = None):
        self.mgr = manager or _vision_manager
        super().__init__(
            ToolMetadata(
                name="screen.capture",
                description="Capture a temporary screenshot with privacy protection.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "mode": {"type": "string", "enum": ["FULL_SCREEN", "ACTIVE_WINDOW", "REGION"], "default": "FULL_SCREEN"},
                    }
                },
                permission_requirement=PermissionCategory.SCREEN_READ,
                risk_level=RiskLevel.LOW,
                verification_strategy="screen_captured"
            )
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        try:
            mode_str = kwargs.get("mode", "FULL_SCREEN")
            mode = CaptureMode(mode_str)
            cap = self.mgr.capture_screen(mode=mode)
            return ToolResult(success=True, data={
                "width": cap["width"],
                "height": cap["height"],
                "active_window": cap["active_window"],
                "source": cap["source"],
                "timestamp": cap["timestamp"]
            })
        except Exception as e:
            return self.handle_error(e)

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class ScreenReadTextTool(BaseTool):
    def __init__(self, manager: Optional[ScreenVisionManager] = None):
        self.mgr = manager or _vision_manager
        super().__init__(
            ToolMetadata(
                name="screen.read_text",
                description="Extract visible text regions from the screen using local OCR.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "mode": {"type": "string", "enum": ["FULL_SCREEN", "ACTIVE_WINDOW"], "default": "FULL_SCREEN"}
                    }
                },
                permission_requirement=PermissionCategory.SCREEN_READ,
                risk_level=RiskLevel.LOW,
                verification_strategy="screen_text_read"
            )
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        try:
            mode_str = kwargs.get("mode", "FULL_SCREEN")
            mode = CaptureMode(mode_str)
            res = self.mgr.read_screen_text(mode=mode)
            return ToolResult(success=True, data=res)
        except Exception as e:
            return self.handle_error(e)

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class ScreenAnalyzeTool(BaseTool):
    def __init__(self, manager: Optional[ScreenVisionManager] = None):
        self.mgr = manager or _vision_manager
        super().__init__(
            ToolMetadata(
                name="screen.analyze",
                description="Analyze screen layout, active window, and detect visual UI elements.",
                input_schema={"type": "object", "properties": {}},
                permission_requirement=PermissionCategory.SCREEN_READ,
                risk_level=RiskLevel.LOW,
                verification_strategy="screen_analyzed"
            )
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        try:
            state = self.mgr.analyze_screen()
            return ToolResult(success=True, data={
                "active_window": state.active_window,
                "screen_size": state.screen_size,
                "visual_summary": state.visual_summary,
                "element_count": len(state.detected_elements),
                "elements": [e.model_dump() for e in state.detected_elements]
            })
        except Exception as e:
            return self.handle_error(e)

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class ScreenDescribeTool(BaseTool):
    def __init__(self, manager: Optional[ScreenVisionManager] = None):
        self.mgr = manager or _vision_manager
        super().__init__(
            ToolMetadata(
                name="screen.describe",
                description="Generate a natural language summary description of the screen.",
                input_schema={"type": "object", "properties": {}},
                permission_requirement=PermissionCategory.SCREEN_READ,
                risk_level=RiskLevel.LOW,
                verification_strategy="screen_described"
            )
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        try:
            desc = self.mgr.describe_screen()
            return ToolResult(success=True, data={"description": desc})
        except Exception as e:
            return self.handle_error(e)

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class ScreenFindTool(BaseTool):
    def __init__(self, manager: Optional[ScreenVisionManager] = None):
        self.mgr = manager or _vision_manager
        super().__init__(
            ToolMetadata(
                name="screen.find",
                description="Find visual element coordinates matching a label or description.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "description": {"type": "string", "description": "Target visual element label"}
                    },
                    "required": ["description"]
                },
                permission_requirement=PermissionCategory.SCREEN_READ,
                risk_level=RiskLevel.LOW,
                verification_strategy="screen_element_found"
            )
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        try:
            elem = self.mgr.find_visual_target(kwargs["description"])
            return ToolResult(success=True, data=elem.model_dump())
        except Exception as e:
            return self.handle_error(e)

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class ScreenCompareTool(BaseTool):
    def __init__(self, manager: Optional[ScreenVisionManager] = None):
        self.mgr = manager or _vision_manager
        super().__init__(
            ToolMetadata(
                name="screen.compare",
                description="Compare visual screen state changes before and after an action.",
                input_schema={"type": "object", "properties": {}},
                permission_requirement=PermissionCategory.SCREEN_READ,
                risk_level=RiskLevel.LOW,
                verification_strategy="screen_compared"
            )
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        try:
            # Captures current screen and compares with baseline state
            state_a = self.mgr.analyze_screen()
            state_b = self.mgr.analyze_screen()
            res = self.mgr.compare_screen_states(state_a, state_b)
            return ToolResult(success=True, data=res.model_dump())
        except Exception as e:
            return self.handle_error(e)

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


SCREEN_TOOLS = [
    ScreenCaptureTool(),
    ScreenReadTextTool(),
    ScreenAnalyzeTool(),
    ScreenDescribeTool(),
    ScreenFindTool(),
    ScreenCompareTool(),
]
