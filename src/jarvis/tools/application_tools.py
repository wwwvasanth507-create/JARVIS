"""
Structured Application Tools for JARVIS.
Exposes application listing, launching, closing, and status verification tools.
"""

from typing import Any, Dict, List, Optional
from jarvis.tools.base import BaseTool, ToolMetadata, ToolResult
from jarvis.security.permissions import PermissionCategory, RiskLevel, PermissionEvaluator
from jarvis.applications.launcher import ApplicationLauncher
from jarvis.applications.registry import ApplicationRegistry
from jarvis.applications.detector import ApplicationDetector

launcher = ApplicationLauncher()
registry = ApplicationRegistry()
evaluator = PermissionEvaluator()


class ApplicationBaseTool(BaseTool):
    """Base class for Application tools enforcing permission security checks."""

    def __init__(self, name: str, description: str, category: PermissionCategory, risk: RiskLevel, schema: Dict[str, Any]):
        meta = ToolMetadata(
            name=name,
            description=description,
            input_schema=schema,
            permission_requirement=category,
            risk_level=risk,
            verification_strategy="process_check",
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


class ListApplicationsTool(ApplicationBaseTool):
    def __init__(self):
        super().__init__(
            name="application.list",
            description="Lists all registered applications and their aliases.",
            category=PermissionCategory.APPLICATION_CONTROL,
            risk=RiskLevel.LOW,
            schema={"type": "object", "properties": {}},
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        perm_err = self._check_permission(self.name, kwargs)
        if perm_err:
            return perm_err

        apps = registry.list_applications()
        return ToolResult(
            success=True,
            data=[a.model_dump() for a in apps],
            error=None,
            verification_details={"verified": True, "count": len(apps)},
        )

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return True


class OpenApplicationTool(ApplicationBaseTool):
    def __init__(self):
        super().__init__(
            name="application.open",
            description="Opens/launches a target application by name or alias (e.g. 'Chrome', 'Notepad', 'Calculator').",
            category=PermissionCategory.APPLICATION_CONTROL,
            risk=RiskLevel.LOW,
            schema={
                "type": "object",
                "properties": {"name": {"type": "string"}},
                "required": ["name"],
            },
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        perm_err = self._check_permission(self.name, kwargs)
        if perm_err:
            return perm_err

        res = launcher.open_application(kwargs["name"])
        return ToolResult(
            success=res.success,
            data=res.data,
            error=None if res.success else res.message,
            verification_details={"verified": res.verified, "status": res.status},
        )

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return bool(execution_result.verification_details and execution_result.verification_details.get("verified"))


class CloseApplicationTool(ApplicationBaseTool):
    def __init__(self):
        super().__init__(
            name="application.close",
            description="Closes an active application gracefully by name or alias.",
            category=PermissionCategory.APPLICATION_CONTROL,
            risk=RiskLevel.MEDIUM,
            schema={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "force": {"type": "boolean", "default": False},
                },
                "required": ["name"],
            },
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        perm_err = self._check_permission(self.name, kwargs)
        if perm_err:
            return perm_err

        res = launcher.close_application(kwargs["name"], force=kwargs.get("force", False))
        return ToolResult(
            success=res.success,
            data=res.data,
            error=None if res.success else res.message,
            verification_details={"verified": res.verified, "status": res.status},
        )

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return bool(execution_result.verification_details and execution_result.verification_details.get("verified"))


class IsApplicationRunningTool(ApplicationBaseTool):
    def __init__(self):
        super().__init__(
            name="application.is_running",
            description="Checks whether a target application is currently running.",
            category=PermissionCategory.APPLICATION_CONTROL,
            risk=RiskLevel.LOW,
            schema={
                "type": "object",
                "properties": {"name": {"type": "string"}},
                "required": ["name"],
            },
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        perm_err = self._check_permission(self.name, kwargs)
        if perm_err:
            return perm_err

        entry = registry.resolve(kwargs["name"])
        status = ApplicationDetector.get_status(entry) if entry else None
        is_running = status.is_running if status else False

        return ToolResult(
            success=True,
            data={"name": kwargs["name"], "is_running": is_running, "status": status.model_dump() if status else None},
            error=None,
            verification_details={"verified": True, "is_running": is_running},
        )

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return True
