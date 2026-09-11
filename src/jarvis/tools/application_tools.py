"""
Structured Application Control Tools for JARVIS Tool Subsystem.
"""

from typing import Any, Dict, Optional
from jarvis.applications.manager import ApplicationManager
from jarvis.security.permissions import PermissionCategory, RiskLevel
from jarvis.tools.base import BaseTool, ToolMetadata, ToolResult


# Global manager instance
_app_manager = ApplicationManager()


def _extract_app_name(kwargs: Dict[str, Any]) -> str:
    val = kwargs.get("name") or kwargs.get("app") or kwargs.get("query") or kwargs.get("app_name") or kwargs.get("target")
    if not val:
        raise ValueError("Missing required application name parameter ('name').")
    return str(val)


class ListApplicationsTool(BaseTool):
    def __init__(self, manager: Optional[ApplicationManager] = None):
        self.mgr = manager or _app_manager
        super().__init__(
            ToolMetadata(
                name="application.list",
                description="List all registered applications and their metadata.",
                input_schema={"type": "object", "properties": {}},
                permission_requirement=PermissionCategory.APPLICATION_CONTROL,
                risk_level=RiskLevel.LOW,
                verification_strategy="apps_listed",
            )
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        try:
            res = self.mgr.list_applications()
            return ToolResult(success=True, data=[a.model_dump() for a in res])
        except Exception as e:
            return self.handle_error(e)

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class FindApplicationTool(BaseTool):
    def __init__(self, manager: Optional[ApplicationManager] = None):
        self.mgr = manager or _app_manager
        super().__init__(
            ToolMetadata(
                name="application.find",
                description="Find an application by query or alias.",
                input_schema={
                    "type": "object",
                    "properties": {"query": {"type": "string"}},
                    "required": ["query"],
                },
                permission_requirement=PermissionCategory.APPLICATION_CONTROL,
                risk_level=RiskLevel.LOW,
                verification_strategy="app_found",
            )
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        try:
            res = self.mgr.find_application(query=_extract_app_name(kwargs))
            return ToolResult(success=True, data=res.model_dump())
        except Exception as e:
            return self.handle_error(e)

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class OpenApplicationTool(BaseTool):
    def __init__(self, manager: Optional[ApplicationManager] = None):
        self.mgr = manager or _app_manager
        super().__init__(
            ToolMetadata(
                name="application.open",
                description="Open/launch an application by name or alias.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "arguments": {"type": "array", "items": {"type": "string"}},
                        "working_directory": {"type": "string"},
                    },
                    "required": ["name"],
                },
                permission_requirement=PermissionCategory.APPLICATION_CONTROL,
                risk_level=RiskLevel.MEDIUM,
                verification_strategy="app_opened",
            )
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        try:
            res = self.mgr.open_application(
                query=_extract_app_name(kwargs),
                arguments=kwargs.get("arguments"),
                working_directory=kwargs.get("working_directory"),
            )
            return ToolResult(success=res.success, data=res.model_dump())
        except Exception as e:
            return self.handle_error(e)

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class CloseApplicationTool(BaseTool):
    def __init__(self, manager: Optional[ApplicationManager] = None):
        self.mgr = manager or _app_manager
        super().__init__(
            ToolMetadata(
                name="application.close",
                description="Close an active application gracefully.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "force": {"type": "boolean", "default": False},
                    },
                    "required": ["name"],
                },
                permission_requirement=PermissionCategory.APPLICATION_CONTROL,
                risk_level=RiskLevel.HIGH,
                verification_strategy="app_closed",
            )
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        try:
            res = self.mgr.close_application(
                query=_extract_app_name(kwargs),
                force=kwargs.get("force", False),
            )
            return ToolResult(success=res.success, data=res.model_dump())
        except Exception as e:
            return self.handle_error(e)

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class RestartApplicationTool(BaseTool):
    def __init__(self, manager: Optional[ApplicationManager] = None):
        self.mgr = manager or _app_manager
        super().__init__(
            ToolMetadata(
                name="application.restart",
                description="Restart an active application safely.",
                input_schema={
                    "type": "object",
                    "properties": {"name": {"type": "string"}},
                    "required": ["name"],
                },
                permission_requirement=PermissionCategory.APPLICATION_CONTROL,
                risk_level=RiskLevel.HIGH,
                verification_strategy="app_restarted",
            )
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        try:
            res = self.mgr.restart_application(query=_extract_app_name(kwargs))
            return ToolResult(success=res.success, data=res.model_dump())
        except Exception as e:
            return self.handle_error(e)

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class IsApplicationRunningTool(BaseTool):
    def __init__(self, manager: Optional[ApplicationManager] = None):
        self.mgr = manager or _app_manager
        super().__init__(
            ToolMetadata(
                name="application.is_running",
                description="Check whether a target application is currently running.",
                input_schema={
                    "type": "object",
                    "properties": {"name": {"type": "string"}},
                    "required": ["name"],
                },
                permission_requirement=PermissionCategory.APPLICATION_CONTROL,
                risk_level=RiskLevel.LOW,
                verification_strategy="app_status_checked",
            )
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        try:
            res = self.mgr.is_running(query=_extract_app_name(kwargs))
            return ToolResult(success=True, data=res.model_dump())
        except Exception as e:
            return self.handle_error(e)

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class ListRunningApplicationsTool(BaseTool):
    def __init__(self, manager: Optional[ApplicationManager] = None):
        self.mgr = manager or _app_manager
        super().__init__(
            ToolMetadata(
                name="application.list_running",
                description="List all currently running registered applications.",
                input_schema={"type": "object", "properties": {}},
                permission_requirement=PermissionCategory.APPLICATION_CONTROL,
                risk_level=RiskLevel.LOW,
                verification_strategy="running_apps_listed",
            )
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        try:
            res = self.mgr.list_running()
            return ToolResult(success=True, data=[s.model_dump() for s in res])
        except Exception as e:
            return self.handle_error(e)

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class FocusApplicationTool(BaseTool):
    def __init__(self, manager: Optional[ApplicationManager] = None):
        self.mgr = manager or _app_manager
        super().__init__(
            ToolMetadata(
                name="application.focus",
                description="Bring target application window to focus.",
                input_schema={
                    "type": "object",
                    "properties": {"name": {"type": "string"}},
                    "required": ["name"],
                },
                permission_requirement=PermissionCategory.APPLICATION_CONTROL,
                risk_level=RiskLevel.MEDIUM,
                verification_strategy="app_focused",
            )
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        try:
            target_name = _extract_app_name(kwargs)
            res = self.mgr.focus_application(query=target_name)
            return ToolResult(success=res, data={"focused": res, "name": target_name})
        except Exception as e:
            return self.handle_error(e)

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class CheckApplicationHealthTool(BaseTool):
    def __init__(self, manager: Optional[ApplicationManager] = None):
        self.mgr = manager or _app_manager
        super().__init__(
            ToolMetadata(
                name="application.health",
                description="Check responsiveness and health status of an application.",
                input_schema={
                    "type": "object",
                    "properties": {"name": {"type": "string"}},
                    "required": ["name"],
                },
                permission_requirement=PermissionCategory.APPLICATION_CONTROL,
                risk_level=RiskLevel.LOW,
                verification_strategy="health_checked",
            )
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        try:
            res = self.mgr.check_health(query=_extract_app_name(kwargs))
            return ToolResult(success=True, data=res.model_dump())
        except Exception as e:
            return self.handle_error(e)

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class OpenApplicationFileTool(BaseTool):
    def __init__(self, manager: Optional[ApplicationManager] = None):
        self.mgr = manager or _app_manager
        super().__init__(
            ToolMetadata(
                name="application.open_file",
                description="Open a file or project path using a target application.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "file_path": {"type": "string"},
                    },
                    "required": ["name", "file_path"],
                },
                permission_requirement=PermissionCategory.APPLICATION_CONTROL,
                risk_level=RiskLevel.MEDIUM,
                verification_strategy="file_opened_in_app",
            )
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        try:
            res = self.mgr.open_file(query=_extract_app_name(kwargs), file_path=kwargs["file_path"])
            return ToolResult(success=res.success, data=res.model_dump())
        except Exception as e:
            return self.handle_error(e)

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class OpenApplicationUrlTool(BaseTool):
    def __init__(self, manager: Optional[ApplicationManager] = None):
        self.mgr = manager or _app_manager
        super().__init__(
            ToolMetadata(
                name="application.open_url",
                description="Open a URL string using default browser application.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "url": {"type": "string"},
                    },
                    "required": ["url"],
                },
                permission_requirement=PermissionCategory.APPLICATION_CONTROL,
                risk_level=RiskLevel.MEDIUM,
                verification_strategy="url_opened",
            )
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        try:
            res = self.mgr.open_url(url_str=kwargs["url"])
            return ToolResult(success=res.success, data=res.model_dump())
        except Exception as e:
            return self.handle_error(e)

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class ListStartupApplicationsTool(BaseTool):
    def __init__(self, manager: Optional[ApplicationManager] = None):
        self.mgr = manager or _app_manager
        super().__init__(
            ToolMetadata(
                name="application.list_startup",
                description="Read-only list of configured system startup applications.",
                input_schema={"type": "object", "properties": {}},
                permission_requirement=PermissionCategory.APPLICATION_CONTROL,
                risk_level=RiskLevel.LOW,
                verification_strategy="startup_listed",
            )
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        try:
            res = self.mgr.list_startup_applications()
            return ToolResult(success=True, data=[s.model_dump() for s in res])
        except Exception as e:
            return self.handle_error(e)

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


APPLICATION_TOOLS = [
    ListApplicationsTool(),
    FindApplicationTool(),
    OpenApplicationTool(),
    CloseApplicationTool(),
    RestartApplicationTool(),
    IsApplicationRunningTool(),
    ListRunningApplicationsTool(),
    FocusApplicationTool(),
    CheckApplicationHealthTool(),
    OpenApplicationFileTool(),
    OpenApplicationUrlTool(),
    ListStartupApplicationsTool(),
]
