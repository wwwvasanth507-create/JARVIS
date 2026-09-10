"""
Skill Executor delegating to Core Orchestration PlanExecutor.
"""

from typing import Optional
from jarvis.core.orchestration.executor import PlanExecutor
from jarvis.core.orchestration.state import ExecutionState
from jarvis.skills.models import SkillDefinition
from jarvis.skills.planner import SkillPlanner


class SkillExecutor:
    """Executes validated skill workflows using core PlanExecutor."""

    def __init__(
        self,
        planner: Optional[SkillPlanner] = None,
        plan_executor: Optional[PlanExecutor] = None,
    ):
        self.planner = planner or SkillPlanner()
        self.plan_executor = plan_executor or PlanExecutor()

    def execute_skill(
        self,
        skill: SkillDefinition,
        intent: Any,
        state: ExecutionState,
        registered_tools: dict,
        confirmation_token: Optional[str] = None,
    ) -> ExecutionState:
        plan = self.planner.create_skill_plan(skill, intent, registered_tools)
        return self.plan_executor.execute_plan(plan, state, confirmation_token=confirmation_token)
