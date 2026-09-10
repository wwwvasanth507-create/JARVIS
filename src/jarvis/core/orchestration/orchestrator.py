"""
Main JarvisOrchestrator Entry Point for JARVIS core.
"""

import uuid
from typing import Any, Dict, Optional
from jarvis.core.orchestration.cancellation import CancellationManager
from jarvis.core.orchestration.context import OrchestrationContext
from jarvis.core.orchestration.dispatcher import ToolDispatcher
from jarvis.core.orchestration.errors import AmbiguousRequestError, PlanValidationError
from jarvis.core.orchestration.executor import PlanExecutor
from jarvis.core.orchestration.goals import GoalResolver
from jarvis.core.orchestration.intent import IntentParser
from jarvis.core.orchestration.planner import Planner
from jarvis.core.orchestration.policy import PlanValidator
from jarvis.core.orchestration.state import ExecutionHistoryEntry, ExecutionState, ExecutionStatus
from jarvis.security.permissions import PermissionEvaluator


from jarvis.skills.manager import SkillManager
from jarvis.skills.planner import SkillPlanner


class JarvisOrchestrator:
    """Primary orchestration manager coordinating intent parsing, planning, validation, execution, and verification."""

    def __init__(
        self,
        intent_parser: Optional[IntentParser] = None,
        goal_resolver: Optional[GoalResolver] = None,
        planner: Optional[Planner] = None,
        plan_validator: Optional[PlanValidator] = None,
        dispatcher: Optional[ToolDispatcher] = None,
        executor: Optional[PlanExecutor] = None,
        cancellation_mgr: Optional[CancellationManager] = None,
        memory_mgr: Optional[MemoryManager] = None,
        skill_mgr: Optional[SkillManager] = None,
    ):
        self.intent_parser = intent_parser or IntentParser()
        self.goal_resolver = goal_resolver or GoalResolver()
        self.planner = planner or Planner()
        self.validator = plan_validator or PlanValidator()
        self.dispatcher = dispatcher or ToolDispatcher()
        self.executor = executor or PlanExecutor(dispatcher=self.dispatcher)
        self.cancellation_mgr = cancellation_mgr or CancellationManager()
        self.memory_mgr = memory_mgr
        self.skill_mgr = skill_mgr
        self.skill_planner = SkillPlanner()
        self.history: list[ExecutionHistoryEntry] = []

    def handle(self, request: str, confirmation_token: Optional[str] = None) -> ExecutionState:
        execution_id = str(uuid.uuid4())
        state = ExecutionState(execution_id=execution_id, request=request)

        # 0. Check for explicit memory statements
        if self.memory_mgr:
            stored_mem = self.memory_mgr.process_user_text_for_memories(request)
            if stored_mem:
                state.status = ExecutionStatus.COMPLETED
                state.observations.append({"stored_memory": stored_mem.model_dump()})
                self._record_history(state, intent_action="memory.remember")
                return state

        # 1. Check for cancellation signals
        if self.cancellation_mgr.is_cancellation_request(request):
            return self.cancellation_mgr.cancel_execution(state, reason="User issued cancellation keyword")

        # 2. Intent Parsing
        try:
            intent = self.intent_parser.parse(request)
        except AmbiguousRequestError as amb:
            state.status = ExecutionStatus.NEEDS_CLARIFICATION
            state.error = str(amb)
            self._record_history(state, intent_action=None)
            return state

        if intent.requires_clarification:
            state.status = ExecutionStatus.NEEDS_CLARIFICATION
            state.error = intent.clarification.question if intent.clarification else "Clarification required."
            self._record_history(state, intent_action=intent.action)
            return state

        state.fast_path_used = intent.is_fast_path

        # 3. Goal Construction
        goal = self.goal_resolver.resolve(intent)
        state.goal = goal

        # 4. Planning (Check skill resolver first)
        resolved_skill = self.skill_mgr.resolve_skill(intent) if self.skill_mgr else None
        if resolved_skill:
            plan = self.skill_planner.create_skill_plan(resolved_skill, intent, self.dispatcher.tools)
        else:
            plan = self.planner.create_plan(intent, goal)

        # 5. Plan Validation
        try:
            self.validator.validate(plan, self.dispatcher.tools)
        except PlanValidationError as pve:
            state.status = ExecutionStatus.FAILED
            state.error = f"Plan validation failed: {pve}"
            self._record_history(state, intent_action=intent.action)
            return state

        # 6. Execution
        state = self.executor.execute_plan(plan, state, confirmation_token=confirmation_token)

        self._record_history(state, intent_action=intent.action)
        return state

    def _record_history(self, state: ExecutionState, intent_action: Optional[str]) -> None:
        duration = (state.end_time - state.start_time) * 1000.0 if state.end_time else 0.0
        verified_all = len(state.verification_results) > 0 and all(
            v.get("verified", False) for v in state.verification_results
        )
        entry = ExecutionHistoryEntry(
            execution_id=state.execution_id,
            request=state.request,
            intent_action=intent_action,
            goal_description=state.goal.description if state.goal else None,
            status=state.status,
            steps_total=len(state.plan.steps) if state.plan else 0,
            steps_completed=len(state.completed_steps),
            duration_ms=duration,
            verified=verified_all,
            error=state.error,
        )
        self.history.append(entry)
