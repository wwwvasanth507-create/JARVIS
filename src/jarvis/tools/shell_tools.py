"""
Structured Shell Tools for JARVIS Tool Subsystem.
"""

from typing import Any, Dict, Optional
from jarvis.security.permissions import PermissionCategory, RiskLevel
from jarvis.shell.manager import ShellManager
from jarvis.tools.base import BaseTool, ToolMetadata, ToolResult


# Global manager instance
_shell_manager = ShellManager()


class ExecuteShellCommandTool(BaseTool):
    def __init__(self, manager: Optional[ShellManager] = None):
        self.mgr = manager or _shell_manager
        super().__init__(
            ToolMetadata(
                name="shell.execute",
                description="Execute a controlled command in terminal/shell with safety checks.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "command": {"type": "string", "description": "Command string to execute"},
                        "working_directory": {"type": "string", "description": "Target working directory path"},
                        "timeout": {"type": "integer", "default": 30},
                        "is_background": {"type": "boolean", "default": False},
                    },
                    "required": ["command"],
                },
                permission_requirement=PermissionCategory.RUN_COMMANDS,
                risk_level=RiskLevel.MEDIUM,
                verification_strategy="command_exit_code",
            )
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        try:
            res = self.mgr.execute(
                command_str=kwargs["command"],
                working_directory=kwargs.get("working_directory"),
                timeout=kwargs.get("timeout", 30),
                is_background=kwargs.get("is_background", False),
            )
            data = res.model_dump()
            return ToolResult(success=True, data=data)
        except Exception as e:
            return self.handle_error(e)

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class GetShellEnvironmentTool(BaseTool):
    def __init__(self, manager: Optional[ShellManager] = None):
        self.mgr = manager or _shell_manager
        super().__init__(
            ToolMetadata(
                name="shell.get_environment",
                description="Get secret-redacted environment variables.",
                input_schema={"type": "object", "properties": {}},
                permission_requirement=PermissionCategory.RUN_COMMANDS,
                risk_level=RiskLevel.LOW,
                verification_strategy="env_read",
            )
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        try:
            res = self.mgr.get_environment()
            return ToolResult(success=True, data=res)
        except Exception as e:
            return self.handle_error(e)

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class GetShellInfoTool(BaseTool):
    def __init__(self, manager: Optional[ShellManager] = None):
        self.mgr = manager or _shell_manager
        super().__init__(
            ToolMetadata(
                name="shell.get_shell_info",
                description="Get OS platform, shell executable path, and available system binaries.",
                input_schema={"type": "object", "properties": {}},
                permission_requirement=PermissionCategory.RUN_COMMANDS,
                risk_level=RiskLevel.LOW,
                verification_strategy="info_read",
            )
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        try:
            res = self.mgr.get_shell_info()
            return ToolResult(success=True, data=res.model_dump())
        except Exception as e:
            return self.handle_error(e)

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class ListProcessesTool(BaseTool):
    def __init__(self, manager: Optional[ShellManager] = None):
        self.mgr = manager or _shell_manager
        super().__init__(
            ToolMetadata(
                name="shell.list_processes",
                description="List running system processes with safe metadata.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "limit": {"type": "integer", "default": 100},
                    },
                },
                permission_requirement=PermissionCategory.RUN_COMMANDS,
                risk_level=RiskLevel.LOW,
                verification_strategy="processes_listed",
            )
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        try:
            res = self.mgr.list_processes(limit=kwargs.get("limit", 100))
            return ToolResult(success=True, data=[p.model_dump() for p in res])
        except Exception as e:
            return self.handle_error(e)

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class GetProcessTool(BaseTool):
    def __init__(self, manager: Optional[ShellManager] = None):
        self.mgr = manager or _shell_manager
        super().__init__(
            ToolMetadata(
                name="shell.get_process",
                description="Get detailed metadata for a process by PID.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "pid": {"type": "integer"},
                    },
                    "required": ["pid"],
                },
                permission_requirement=PermissionCategory.RUN_COMMANDS,
                risk_level=RiskLevel.LOW,
                verification_strategy="process_read",
            )
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        try:
            res = self.mgr.get_process(pid=kwargs["pid"])
            return ToolResult(success=True, data=res.model_dump())
        except Exception as e:
            return self.handle_error(e)

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class TerminateProcessTool(BaseTool):
    def __init__(self, manager: Optional[ShellManager] = None):
        self.mgr = manager or _shell_manager
        super().__init__(
            ToolMetadata(
                name="shell.terminate_process",
                description="Terminate a system process by PID safely.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "pid": {"type": "integer"},
                        "force": {"type": "boolean", "default": False},
                    },
                    "required": ["pid"],
                },
                permission_requirement=PermissionCategory.RUN_COMMANDS,
                risk_level=RiskLevel.HIGH,
                verification_strategy="process_terminated",
            )
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        try:
            res = self.mgr.terminate_process(
                pid=kwargs["pid"],
                force=kwargs.get("force", False),
            )
            return ToolResult(success=True, data={"terminated": res, "pid": kwargs["pid"]})
        except Exception as e:
            return self.handle_error(e)

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class JobStatusTool(BaseTool):
    def __init__(self, manager: Optional[ShellManager] = None):
        self.mgr = manager or _shell_manager
        super().__init__(
            ToolMetadata(
                name="shell.job_status",
                description="Check status of a background shell job.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "job_id": {"type": "string"},
                    },
                    "required": ["job_id"],
                },
                permission_requirement=PermissionCategory.RUN_COMMANDS,
                risk_level=RiskLevel.LOW,
                verification_strategy="job_status_read",
            )
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        try:
            res = self.mgr.get_job_status(job_id=kwargs["job_id"])
            return ToolResult(success=True, data=res.model_dump())
        except Exception as e:
            return self.handle_error(e)

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class JobOutputTool(BaseTool):
    def __init__(self, manager: Optional[ShellManager] = None):
        self.mgr = manager or _shell_manager
        super().__init__(
            ToolMetadata(
                name="shell.job_output",
                description="Get stdout/stderr output for a background job.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "job_id": {"type": "string"},
                    },
                    "required": ["job_id"],
                },
                permission_requirement=PermissionCategory.RUN_COMMANDS,
                risk_level=RiskLevel.LOW,
                verification_strategy="job_output_read",
            )
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        try:
            res = self.mgr.get_job_status(job_id=kwargs["job_id"])
            return ToolResult(
                success=True,
                data={
                    "job_id": res.job_id,
                    "status": res.status,
                    "stdout": res.stdout,
                    "stderr": res.stderr,
                    "exit_code": res.exit_code,
                },
            )
        except Exception as e:
            return self.handle_error(e)

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class CancelJobTool(BaseTool):
    def __init__(self, manager: Optional[ShellManager] = None):
        self.mgr = manager or _shell_manager
        super().__init__(
            ToolMetadata(
                name="shell.cancel",
                description="Cancel a running background shell job.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "job_id": {"type": "string"},
                    },
                    "required": ["job_id"],
                },
                permission_requirement=PermissionCategory.RUN_COMMANDS,
                risk_level=RiskLevel.MEDIUM,
                verification_strategy="job_cancelled",
            )
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        try:
            res = self.mgr.cancel_job(job_id=kwargs["job_id"])
            return ToolResult(success=True, data=res.model_dump())
        except Exception as e:
            return self.handle_error(e)

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


SHELL_TOOLS = [
    ExecuteShellCommandTool(),
    GetShellEnvironmentTool(),
    GetShellInfoTool(),
    ListProcessesTool(),
    GetProcessTool(),
    TerminateProcessTool(),
    JobStatusTool(),
    JobOutputTool(),
    CancelJobTool(),
]
