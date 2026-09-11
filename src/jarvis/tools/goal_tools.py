"""
Structured Goal Management Tools for JARVIS Tool Subsystem.
"""

from typing import Any, Dict, Optional
from jarvis.core.goals.manager import GoalManager
from jarvis.core.goals.models import GoalStatus, GoalPriority, AutonomyLevel, GoalOwner, DeadlineType
from jarvis.security.permissions import PermissionCategory, RiskLevel
from jarvis.tools.base import BaseTool, ToolMetadata, ToolResult

# Shared GoalManager instance
_goal_manager = GoalManager()


class CreateGoalTool(BaseTool):
    def __init__(self, manager: Optional[GoalManager] = None):
        self.mgr = manager or _goal_manager
        super().__init__(
            ToolMetadata(
                name="goal.create",
                description="Create a new structured autonomous goal with objectives.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "description": {"type": "string"},
                        "priority": {"type": "string", "default": "NORMAL"},
                        "autonomy_level": {"type": "integer", "default": 1},
                        "template_id": {"type": "string"},
                        "associated_project": {"type": "string"},
                    },
                    "required": ["title"],
                },
                permission_requirement=PermissionCategory.SYSTEM_CONTROL,
                risk_level=RiskLevel.MEDIUM,
                verification_strategy="goal_created",
            )
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        try:
            prio = GoalPriority(kwargs.get("priority", "NORMAL").upper())
            autonomy = AutonomyLevel(kwargs.get("autonomy_level", 1))
            g = self.mgr.create_goal(
                title=kwargs["title"],
                description=kwargs.get("description", ""),
                priority=prio,
                autonomy_level=autonomy,
                template_id=kwargs.get("template_id"),
                associated_project=kwargs.get("associated_project"),
            )
            return ToolResult(success=True, data=g.model_dump())
        except Exception as e:
            return self.handle_error(e)

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class PreviewGoalTool(BaseTool):
    def __init__(self, manager: Optional[GoalManager] = None):
        self.mgr = manager or _goal_manager
        super().__init__(
            ToolMetadata(
                name="goal.preview",
                description="Generate a goal proposal from natural language prompt.",
                input_schema={
                    "type": "object",
                    "properties": {"request": {"type": "string"}},
                    "required": ["request"],
                },
                permission_requirement=PermissionCategory.SYSTEM_CONTROL,
                risk_level=RiskLevel.LOW,
                verification_strategy="proposal_generated",
            )
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        try:
            prop = self.mgr.propose_goal_from_intent(kwargs["request"])
            return ToolResult(success=True, data=prop)
        except Exception as e:
            return self.handle_error(e)

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class ActivateGoalTool(BaseTool):
    def __init__(self, manager: Optional[GoalManager] = None):
        self.mgr = manager or _goal_manager
        super().__init__(
            ToolMetadata(
                name="goal.activate",
                description="Activate a draft or paused goal.",
                input_schema={
                    "type": "object",
                    "properties": {"goal_id": {"type": "string"}},
                    "required": ["goal_id"],
                },
                permission_requirement=PermissionCategory.SYSTEM_CONTROL,
                risk_level=RiskLevel.MEDIUM,
                verification_strategy="goal_activated",
            )
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        try:
            g = self.mgr.activate_goal(kwargs["goal_id"])
            return ToolResult(success=True, data=g.model_dump())
        except Exception as e:
            return self.handle_error(e)

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class PauseGoalTool(BaseTool):
    def __init__(self, manager: Optional[GoalManager] = None):
        self.mgr = manager or _goal_manager
        super().__init__(
            ToolMetadata(
                name="goal.pause",
                description="Pause an active goal.",
                input_schema={
                    "type": "object",
                    "properties": {"goal_id": {"type": "string"}},
                    "required": ["goal_id"],
                },
                permission_requirement=PermissionCategory.SYSTEM_CONTROL,
                risk_level=RiskLevel.LOW,
                verification_strategy="goal_paused",
            )
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        try:
            g = self.mgr.pause_goal(kwargs["goal_id"])
            return ToolResult(success=True, data=g.model_dump())
        except Exception as e:
            return self.handle_error(e)

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class ResumeGoalTool(BaseTool):
    def __init__(self, manager: Optional[GoalManager] = None):
        self.mgr = manager or _goal_manager
        super().__init__(
            ToolMetadata(
                name="goal.resume",
                description="Resume a paused goal.",
                input_schema={
                    "type": "object",
                    "properties": {"goal_id": {"type": "string"}},
                    "required": ["goal_id"],
                },
                permission_requirement=PermissionCategory.SYSTEM_CONTROL,
                risk_level=RiskLevel.LOW,
                verification_strategy="goal_resumed",
            )
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        try:
            g = self.mgr.resume_goal(kwargs["goal_id"])
            return ToolResult(success=True, data=g.model_dump())
        except Exception as e:
            return self.handle_error(e)

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class CancelGoalTool(BaseTool):
    def __init__(self, manager: Optional[GoalManager] = None):
        self.mgr = manager or _goal_manager
        super().__init__(
            ToolMetadata(
                name="goal.cancel",
                description="Cancel an active or paused goal.",
                input_schema={
                    "type": "object",
                    "properties": {"goal_id": {"type": "string"}},
                    "required": ["goal_id"],
                },
                permission_requirement=PermissionCategory.SYSTEM_CONTROL,
                risk_level=RiskLevel.MEDIUM,
                verification_strategy="goal_cancelled",
            )
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        try:
            g = self.mgr.cancel_goal(kwargs["goal_id"])
            return ToolResult(success=True, data=g.model_dump())
        except Exception as e:
            return self.handle_error(e)

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class ListGoalsTool(BaseTool):
    def __init__(self, manager: Optional[GoalManager] = None):
        self.mgr = manager or _goal_manager
        super().__init__(
            ToolMetadata(
                name="goal.list",
                description="List registered goals with filtering options.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "status": {"type": "string"},
                        "priority": {"type": "string"},
                        "limit": {"type": "integer", "default": 50},
                    },
                },
                permission_requirement=PermissionCategory.SYSTEM_CONTROL,
                risk_level=RiskLevel.LOW,
                verification_strategy="goals_listed",
            )
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        try:
            st = GoalStatus(kwargs["status"]) if kwargs.get("status") else None
            prio = GoalPriority(kwargs["priority"]) if kwargs.get("priority") else None
            goals = self.mgr.list_goals(status=st, priority=prio, limit=kwargs.get("limit", 50))
            return ToolResult(success=True, data=[g.model_dump() for g in goals])
        except Exception as e:
            return self.handle_error(e)

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class GetGoalTool(BaseTool):
    def __init__(self, manager: Optional[GoalManager] = None):
        self.mgr = manager or _goal_manager
        super().__init__(
            ToolMetadata(
                name="goal.get",
                description="Fetch detailed state and objectives of a specific goal.",
                input_schema={
                    "type": "object",
                    "properties": {"goal_id": {"type": "string"}},
                    "required": ["goal_id"],
                },
                permission_requirement=PermissionCategory.SYSTEM_CONTROL,
                risk_level=RiskLevel.LOW,
                verification_strategy="goal_fetched",
            )
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        try:
            g = self.mgr.repo.get_goal(kwargs["goal_id"])
            if not g:
                return ToolResult(success=False, error=f"Goal '{kwargs['goal_id']}' not found.")
            return ToolResult(success=True, data=g.model_dump())
        except Exception as e:
            return self.handle_error(e)

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class ExplainGoalTool(BaseTool):
    def __init__(self, manager: Optional[GoalManager] = None):
        self.mgr = manager or _goal_manager
        super().__init__(
            ToolMetadata(
                name="goal.explain",
                description="Return structured explanation of goal status, priority, and progress.",
                input_schema={
                    "type": "object",
                    "properties": {"goal_id": {"type": "string"}},
                    "required": ["goal_id"],
                },
                permission_requirement=PermissionCategory.SYSTEM_CONTROL,
                risk_level=RiskLevel.LOW,
                verification_strategy="goal_explained",
            )
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        try:
            exp = self.mgr.explain_goal(kwargs["goal_id"])
            return ToolResult(success=True, data=exp)
        except Exception as e:
            return self.handle_error(e)

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class GoalProgressTool(BaseTool):
    def __init__(self, manager: Optional[GoalManager] = None):
        self.mgr = manager or _goal_manager
        super().__init__(
            ToolMetadata(
                name="goal.progress",
                description="Calculate progress %, confidence, and health score for a goal.",
                input_schema={
                    "type": "object",
                    "properties": {"goal_id": {"type": "string"}},
                    "required": ["goal_id"],
                },
                permission_requirement=PermissionCategory.SYSTEM_CONTROL,
                risk_level=RiskLevel.LOW,
                verification_strategy="progress_calculated",
            )
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        try:
            prog = self.mgr.get_goal_progress(kwargs["goal_id"])
            return ToolResult(success=True, data=prog.model_dump())
        except Exception as e:
            return self.handle_error(e)

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


GOAL_TOOLS = [
    CreateGoalTool(),
    PreviewGoalTool(),
    ActivateGoalTool(),
    PauseGoalTool(),
    ResumeGoalTool(),
    CancelGoalTool(),
    ListGoalsTool(),
    GetGoalTool(),
    ExplainGoalTool(),
    GoalProgressTool(),
]
