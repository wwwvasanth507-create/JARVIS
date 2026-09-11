"""
Semantic Computer Control Tools for JARVIS.

Exposes high-level semantic interactor actions (find, click, type, wait, fill form, select table row, drag)
to the LLM brain and orchestrator.
"""

from typing import Any, Dict, List, Optional
from jarvis.tools.base import BaseTool, ToolMetadata, ToolResult
from jarvis.security.permissions import PermissionCategory, RiskLevel, PermissionEvaluator
from jarvis.computer.vision.target_query import TargetQuery

evaluator = PermissionEvaluator()


class SemanticBaseTool(BaseTool):
    """Base class for Semantic Interaction tools enforcing permission security checks."""

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


class FindElementTool(SemanticBaseTool):
    def __init__(self):
        super().__init__(
            name="computer.find_element",
            description="Finds a desktop or web UI element by semantic role, name, text, or spatial query.",
            category=PermissionCategory.SCREEN_READ,
            risk=RiskLevel.LOW,
            schema={
                "type": "object",
                "properties": {
                    "role": {"type": "string"},
                    "name": {"type": "string"},
                    "text": {"type": "string"},
                    "relation": {"type": "string"},
                    "relative_to_label": {"type": "string"},
                },
            },
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        perm = self._check_permission(self.name, kwargs)
        if perm:
            return perm
        from jarvis.computer.semantic_interactor import SemanticComputerInteractor
        interactor = SemanticComputerInteractor.get_instance()
        q = TargetQuery(**kwargs)
        elem = interactor.find_element(q)
        return ToolResult(
            success=elem is not None,
            data=elem.model_dump() if elem else None,
            error=None if elem else f"Element matching '{kwargs}' not found",
        )

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class ClickElementTool(SemanticBaseTool):
    def __init__(self):
        super().__init__(
            name="computer.click_element",
            description="Clicks a desktop/web UI element by semantic target query.",
            category=PermissionCategory.COMPUTER_CONTROL,
            risk=RiskLevel.LOW,
            schema={
                "type": "object",
                "properties": {
                    "role": {"type": "string"},
                    "name": {"type": "string"},
                    "text": {"type": "string"},
                    "relation": {"type": "string"},
                    "relative_to_label": {"type": "string"},
                },
            },
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        perm = self._check_permission(self.name, kwargs)
        if perm:
            return perm
        from jarvis.computer.semantic_interactor import SemanticComputerInteractor
        interactor = SemanticComputerInteractor.get_instance()
        q = TargetQuery(**kwargs)
        res = interactor.click_element(q)
        return ToolResult(
            success=res.success,
            data=res.data,
            error=res.error,
            verification_details=res.verification_details,
        )

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class TypeElementTool(SemanticBaseTool):
    def __init__(self):
        super().__init__(
            name="computer.type_element",
            description="Types text into a target semantic input element.",
            category=PermissionCategory.COMPUTER_CONTROL,
            risk=RiskLevel.MEDIUM,
            schema={
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "target_name": {"type": "string"},
                    "role": {"type": "string", "default": "input"},
                    "sensitive": {"type": "boolean", "default": False},
                },
                "required": ["text"],
            },
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        perm = self._check_permission(self.name, kwargs)
        if perm:
            return perm
        from jarvis.computer.semantic_interactor import SemanticComputerInteractor
        interactor = SemanticComputerInteractor.get_instance()
        q = TargetQuery(name=kwargs.get("target_name"), role=kwargs.get("role", "input"))
        res = interactor.type_into_element(q, kwargs["text"], sensitive=kwargs.get("sensitive", False))
        return ToolResult(
            success=res.success,
            data=res.data,
            error=res.error,
            verification_details=res.verification_details,
        )

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class WaitElementTool(SemanticBaseTool):
    def __init__(self):
        super().__init__(
            name="computer.wait_element",
            description="Waits until a semantic UI element or condition appears.",
            category=PermissionCategory.SCREEN_READ,
            risk=RiskLevel.LOW,
            schema={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "role": {"type": "string"},
                    "timeout_sec": {"type": "number", "default": 10.0},
                },
            },
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        perm = self._check_permission(self.name, kwargs)
        if perm:
            return perm
        from jarvis.computer.semantic_interactor import SemanticComputerInteractor
        interactor = SemanticComputerInteractor.get_instance()
        q = TargetQuery(name=kwargs.get("name"), role=kwargs.get("role"))
        res = interactor.wait_for_element(q, timeout_sec=kwargs.get("timeout_sec", 10.0))
        return ToolResult(success=res.success, data=res.data, error=res.error)

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class FillFormTool(SemanticBaseTool):
    def __init__(self):
        super().__init__(
            name="computer.fill_form",
            description="Fills out a UI form with structured key-value field data.",
            category=PermissionCategory.COMPUTER_CONTROL,
            risk=RiskLevel.MEDIUM,
            schema={
                "type": "object",
                "properties": {
                    "form_data": {"type": "object"},
                },
                "required": ["form_data"],
            },
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        perm = self._check_permission(self.name, kwargs)
        if perm:
            return perm
        from jarvis.computer.semantic_interactor import SemanticComputerInteractor
        interactor = SemanticComputerInteractor.get_instance()
        res = interactor.fill_form(kwargs["form_data"])
        return ToolResult(
            success=res.success,
            data=res.data,
            error=res.error,
            verification_details=res.verification_details,
        )

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


SEMANTIC_TOOLS = [
    FindElementTool(),
    ClickElementTool(),
    TypeElementTool(),
    WaitElementTool(),
    FillFormTool(),
]
