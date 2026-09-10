"""
Structured Clipboard Tools for JARVIS.

Exposes computer.read_clipboard, computer.write_clipboard, computer.clear_clipboard, and computer.inspect_clipboard.
"""

from typing import Any, Dict, List
from jarvis.tools.base import BaseTool, ToolMetadata, ToolResult
from jarvis.security.permissions import PermissionCategory, RiskLevel, PermissionEvaluator
from jarvis.computer.clipboard import ClipboardController

evaluator = PermissionEvaluator()


class ClipboardBaseTool(BaseTool):
    def __init__(self, name: str, description: str, risk: RiskLevel, schema: Dict[str, Any]):
        meta = ToolMetadata(
            name=name,
            description=description,
            input_schema=schema,
            permission_requirement=PermissionCategory.COMPUTER_CONTROL,
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

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class ReadClipboardTool(ClipboardBaseTool):
    def __init__(self):
        super().__init__(
            name="computer.read_clipboard",
            description="Reads text content from the system clipboard safely.",
            risk=RiskLevel.LOW,
            schema={"type": "object", "properties": {}},
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        err = self._check_permission(self.name, kwargs)
        if err:
            return err
        info = ClipboardController.inspect()
        text = ClipboardController.get_text()
        if info["contains_potential_credential"]:
            return ToolResult(success=True, data={"text": "[REDACTED CREDENTIAL]", "info": info})
        return ToolResult(success=True, data={"text": text, "info": info})


class WriteClipboardTool(ClipboardBaseTool):
    def __init__(self):
        super().__init__(
            name="computer.write_clipboard",
            description="Writes text content to the system clipboard.",
            risk=RiskLevel.LOW,
            schema={
                "type": "object",
                "properties": {"text": {"type": "string"}},
                "required": ["text"],
            },
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        err = self._check_permission(self.name, kwargs)
        if err:
            return err
        text = kwargs.get("text", "")
        success = ClipboardController.set_text(text)
        return ToolResult(success=success, data={"written_length": len(text)})


class ClearClipboardTool(ClipboardBaseTool):
    def __init__(self):
        super().__init__(
            name="computer.clear_clipboard",
            description="Clears all content from the system clipboard.",
            risk=RiskLevel.LOW,
            schema={"type": "object", "properties": {}},
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        err = self._check_permission(self.name, kwargs)
        if err:
            return err
        success = ClipboardController.clear()
        return ToolResult(success=success, data={"cleared": True})


class InspectClipboardTool(ClipboardBaseTool):
    def __init__(self):
        super().__init__(
            name="computer.inspect_clipboard",
            description="Inspects system clipboard metadata without returning full sensitive payload.",
            risk=RiskLevel.LOW,
            schema={"type": "object", "properties": {}},
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        err = self._check_permission(self.name, kwargs)
        if err:
            return err
        info = ClipboardController.inspect()
        return ToolResult(success=True, data=info)


CLIPBOARD_TOOLS = [
    ReadClipboardTool(),
    WriteClipboardTool(),
    ClearClipboardTool(),
    InspectClipboardTool(),
]
