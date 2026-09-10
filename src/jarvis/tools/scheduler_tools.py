"""
Task Scheduler Tool definitions for JARVIS tool registry.
"""

from typing import Any, Dict, List, Optional
from jarvis.scheduler.manager import SchedulerManager
from jarvis.security.permissions import PermissionCategory, RiskLevel
from jarvis.tools.base import BaseTool, ToolMetadata, ToolResult


class _BaseSchedulerTool(BaseTool):
    """Base class for scheduler tools providing lazy manager initialization."""

    def __init__(self, metadata: ToolMetadata, manager: Optional[SchedulerManager] = None):
        super().__init__(metadata)
        self._manager_override = manager

    @property
    def mgr(self) -> SchedulerManager:
        if self._manager_override is not None:
            return self._manager_override
        return SchedulerManager()


class SchedulerCreateTool(_BaseSchedulerTool):
    def __init__(self, manager: Optional[SchedulerManager] = None):
        super().__init__(
            ToolMetadata(
                name="scheduler.create",
                description="Create a new scheduled task or reminder.",
                permission_requirement=PermissionCategory.SYSTEM_CONTROL,
                risk_level=RiskLevel.LOW,
                verification_strategy="task_created",
                input_schema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Name or topic of the reminder/task"},
                        "schedule_expression": {"type": "string", "description": "Schedule expression (e.g. 'in 30 minutes', 'tomorrow at 9 AM', 'every Monday at 10 AM')"},
                        "action": {"type": "string", "description": "Action request string or prompt"},
                        "tool_name": {"type": "string", "description": "Optional specific tool name"},
                        "notification_type": {"type": "string", "enum": ["TEXT", "DESKTOP", "VOICE"], "default": "TEXT"},
                    },
                    "required": ["name", "schedule_expression"],
                },
            ),
            manager=manager,
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        try:
            task = self.mgr.create_scheduled_task(
                name=kwargs["name"],
                schedule_expression=kwargs["schedule_expression"],
                action=kwargs.get("action", kwargs["name"]),
                tool_name=kwargs.get("tool_name"),
                notification_type=kwargs.get("notification_type", "TEXT"),
            )
            return ToolResult(
                success=True,
                message=f"Created scheduled task '{task.name}' (ID: {task.task_id})",
                data=task.model_dump(),
            )
        except Exception as e:
            return self.handle_error(e)

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class SchedulerListTool(_BaseSchedulerTool):
    def __init__(self, manager: Optional[SchedulerManager] = None):
        super().__init__(
            ToolMetadata(
                name="scheduler.list",
                description="List all scheduled tasks and reminders.",
                permission_requirement=PermissionCategory.SYSTEM_CONTROL,
                risk_level=RiskLevel.LOW,
                verification_strategy="task_list_read",
                input_schema={
                    "type": "object",
                    "properties": {
                        "include_disabled": {"type": "boolean", "default": False},
                    },
                },
            ),
            manager=manager,
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        try:
            tasks = self.mgr.list_tasks(include_disabled=kwargs.get("include_disabled", False))
            return ToolResult(
                success=True,
                data={"tasks": [t.model_dump() for t in tasks]},
            )
        except Exception as e:
            return self.handle_error(e)

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class SchedulerGetTool(_BaseSchedulerTool):
    def __init__(self, manager: Optional[SchedulerManager] = None):
        super().__init__(
            ToolMetadata(
                name="scheduler.get",
                description="Get details of a specific scheduled task by ID.",
                permission_requirement=PermissionCategory.SYSTEM_CONTROL,
                risk_level=RiskLevel.LOW,
                verification_strategy="task_get_read",
                input_schema={
                    "type": "object",
                    "properties": {
                        "task_id": {"type": "string", "description": "Scheduled task ID"},
                    },
                    "required": ["task_id"],
                },
            ),
            manager=manager,
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        try:
            task = self.mgr.get_task(kwargs["task_id"])
            if not task:
                return ToolResult(success=False, error=f"Task '{kwargs['task_id']}' not found.")
            return ToolResult(success=True, data=task.model_dump())
        except Exception as e:
            return self.handle_error(e)

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class SchedulerCancelTool(_BaseSchedulerTool):
    def __init__(self, manager: Optional[SchedulerManager] = None):
        super().__init__(
            ToolMetadata(
                name="scheduler.cancel",
                description="Cancel a scheduled task or reminder.",
                permission_requirement=PermissionCategory.SYSTEM_CONTROL,
                risk_level=RiskLevel.LOW,
                verification_strategy="task_cancelled",
                input_schema={
                    "type": "object",
                    "properties": {
                        "task_id": {"type": "string", "description": "Scheduled task ID to cancel"},
                    },
                    "required": ["task_id"],
                },
            ),
            manager=manager,
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        try:
            res = self.mgr.cancel_task(kwargs["task_id"])
            if not res:
                return ToolResult(success=False, error=f"Task '{kwargs['task_id']}' not found or could not be cancelled.")
            return ToolResult(success=True, data={"task_id": kwargs["task_id"], "cancelled": True})
        except Exception as e:
            return self.handle_error(e)

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class SchedulerPauseTool(_BaseSchedulerTool):
    def __init__(self, manager: Optional[SchedulerManager] = None):
        super().__init__(
            ToolMetadata(
                name="scheduler.pause",
                description="Pause a recurring or scheduled task.",
                permission_requirement=PermissionCategory.SYSTEM_CONTROL,
                risk_level=RiskLevel.LOW,
                verification_strategy="task_paused",
                input_schema={
                    "type": "object",
                    "properties": {
                        "task_id": {"type": "string", "description": "Scheduled task ID"},
                    },
                    "required": ["task_id"],
                },
            ),
            manager=manager,
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        try:
            res = self.mgr.pause_task(kwargs["task_id"])
            if not res:
                return ToolResult(success=False, error=f"Task '{kwargs['task_id']}' not found.")
            return ToolResult(success=True, data={"task_id": kwargs["task_id"], "paused": True})
        except Exception as e:
            return self.handle_error(e)

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class SchedulerResumeTool(_BaseSchedulerTool):
    def __init__(self, manager: Optional[SchedulerManager] = None):
        super().__init__(
            ToolMetadata(
                name="scheduler.resume",
                description="Resume a paused task.",
                permission_requirement=PermissionCategory.SYSTEM_CONTROL,
                risk_level=RiskLevel.LOW,
                verification_strategy="task_resumed",
                input_schema={
                    "type": "object",
                    "properties": {
                        "task_id": {"type": "string", "description": "Scheduled task ID"},
                    },
                    "required": ["task_id"],
                },
            ),
            manager=manager,
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        try:
            res = self.mgr.resume_task(kwargs["task_id"])
            if not res:
                return ToolResult(success=False, error=f"Task '{kwargs['task_id']}' not found.")
            return ToolResult(success=True, data={"task_id": kwargs["task_id"], "resumed": True})
        except Exception as e:
            return self.handle_error(e)

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class SchedulerHistoryTool(_BaseSchedulerTool):
    def __init__(self, manager: Optional[SchedulerManager] = None):
        super().__init__(
            ToolMetadata(
                name="scheduler.history",
                description="Get execution run history for scheduled tasks.",
                permission_requirement=PermissionCategory.SYSTEM_CONTROL,
                risk_level=RiskLevel.LOW,
                verification_strategy="task_history_read",
                input_schema={
                    "type": "object",
                    "properties": {
                        "task_id": {"type": "string"},
                        "limit": {"type": "integer", "default": 20},
                    },
                },
            ),
            manager=manager,
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        try:
            runs = self.mgr.list_history(task_id=kwargs.get("task_id"), limit=kwargs.get("limit", 20))
            return ToolResult(
                success=True,
                data={"runs": [r.model_dump() for r in runs]},
            )
        except Exception as e:
            return self.handle_error(e)

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class SchedulerStatusTool(_BaseSchedulerTool):
    def __init__(self, manager: Optional[SchedulerManager] = None):
        super().__init__(
            ToolMetadata(
                name="scheduler.status",
                description="Get health status of the background task scheduler.",
                permission_requirement=PermissionCategory.SYSTEM_CONTROL,
                risk_level=RiskLevel.LOW,
                verification_strategy="scheduler_status_read",
                input_schema={"type": "object", "properties": {}},
            ),
            manager=manager,
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        try:
            st = self.mgr.get_status()
            return ToolResult(success=True, data=st)
        except Exception as e:
            return self.handle_error(e)

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success
