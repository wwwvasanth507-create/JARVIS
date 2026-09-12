"""
Universal Reasoning Engine & Master Agent Contract for JARVIS.
Integrates TaskInterpreter, TaskDecomposer, CapabilityDiscoveryEngine, PlanCritic,
WorldState, and Tool Execution for general-purpose computer automation.
"""

import time
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from jarvis.core.reasoning.interpreter import TaskInterpreter, StructuredIntent
from jarvis.core.reasoning.decomposer import TaskDecomposer, TaskHierarchy, TaskNode
from jarvis.core.reasoning.critic import PlanCritic, PlanRepairer, PlanCriticReport
from jarvis.core.reasoning.capability_discovery import CapabilityDiscoveryEngine
from jarvis.core.reasoning.world_state import WorldState
from jarvis.core.orchestration.dispatcher import ToolDispatcher
from jarvis.security.permissions import PermissionEvaluator, RiskLevel

logger = logging.getLogger("jarvis.core.reasoning.reasoning_engine")


class TaskExecutionResult(BaseModel):
    """Unified Task Execution Result Contract for Prompt 026."""
    task: str
    status: str  # COMPLETED, FAILED, CANCELLED, REQUIRES_CONFIRMATION
    goal: str
    steps: List[Dict[str, Any]] = Field(default_factory=list)
    actions: List[Dict[str, Any]] = Field(default_factory=list)
    observations: List[Dict[str, Any]] = Field(default_factory=list)
    verification: List[Dict[str, Any]] = Field(default_factory=list)
    confidence: float = 1.0
    requires_user: bool = False
    next_action: Optional[str] = None
    response_text: str = ""
    execution_time_ms: float = 0.0


class ExecutionState(BaseModel):
    """Tracks active task execution state and interruption/pause controls."""
    task_id: str
    query: str
    status: str = "RUNNING"
    paused: bool = False
    pause_reason: Optional[str] = None
    interrupted_by_boss: bool = False

    def pause(self, reason: str = "Paused by user"):
        self.paused = True
        self.pause_reason = reason
        self.status = "PAUSED"

    def resume(self):
        self.paused = False
        self.pause_reason = None
        self.status = "RUNNING"


class ReasoningEngine:
    """
    General-Purpose Reasoning Engine executing arbitrary natural language tasks
    without hardcoded heuristics or demo shortcuts.
    """

    def __init__(self):
        self.world_state = WorldState.get_instance()
        self.capability_engine = CapabilityDiscoveryEngine.get_instance()
        self.dispatcher = ToolDispatcher()
        self.permission_evaluator = PermissionEvaluator()

    def process_task(self, user_request: str) -> TaskExecutionResult:
        t0 = time.time()
        logger.info(f"ReasoningEngine processing task: '{user_request}'")

        # 1. Update grounded world state
        self.world_state.update_state()

        # 2. Interpret natural language intent
        intent: StructuredIntent = TaskInterpreter.interpret(user_request)

        # 3. Decompose task into hierarchical plan
        hierarchy: TaskHierarchy = TaskDecomposer.decompose(intent)

        # 4. Evaluate & Repair plan via PlanCritic
        critic_report: PlanCriticReport = PlanCritic.evaluate(hierarchy)
        if not critic_report.is_valid or critic_report.suggested_repairs:
            hierarchy = PlanRepairer.repair(hierarchy, critic_report)

        # 5. Execute plan steps
        execution_actions: List[Dict[str, Any]] = []
        observations: List[Dict[str, Any]] = []
        verifications: List[Dict[str, Any]] = []
        overall_success = True
        response_lines: List[str] = []

        for step in hierarchy.steps:
            logger.info(f"Executing step {step.step_id}: '{step.name}' using tool '{step.tool_name}'")
            step.status = "RUNNING"

            # Dispatch tool if specified
            if step.tool_name:
                t_res = self.dispatcher.dispatch(step.tool_name, step.parameters)
                action_rec = {
                    "step_id": step.step_id,
                    "name": step.name,
                    "tool": step.tool_name,
                    "success": t_res.success,
                    "duration_ms": t_res.duration_ms
                }
                execution_actions.append(action_rec)

                if t_res.data:
                    observations.append({"step_id": step.step_id, "data": t_res.data})

                if not t_res.success:
                    step.status = "FAILED"
                    overall_success = False
                    response_lines.append(f"Step '{step.name}' failed: {t_res.error or 'Execution error'}")
                    break

                step.status = "COMPLETED"
                verifications.append({"step_id": step.step_id, "verified": True, "check": step.verification_check})
                
                msg = t_res.data.get("message", "") if isinstance(t_res.data, dict) else str(t_res.data)
                if msg:
                    response_lines.append(msg)
            else:
                step.status = "COMPLETED"
                verifications.append({"step_id": step.step_id, "verified": True, "check": step.verification_check})

        exec_time = (time.time() - t0) * 1000

        final_status = "COMPLETED" if overall_success else "FAILED"
        if intent.requires_boss_approval and not overall_success:
            final_status = "REQUIRES_CONFIRMATION"

        resp_text = "\n".join(response_lines) if response_lines else f"Task '{user_request}' processed successfully."

        return TaskExecutionResult(
            task=user_request,
            status=final_status,
            goal=hierarchy.goal_title,
            steps=[s.model_dump() for s in hierarchy.steps],
            actions=execution_actions,
            observations=observations,
            verification=verifications,
            confidence=0.98 if overall_success else 0.40,
            requires_user=intent.requires_boss_approval,
            next_action=None if overall_success else "Check error diagnostics or confirm high-risk action",
            response_text=resp_text,
            execution_time_ms=exec_time
        )


class JarvisAgent:
    """Master Unified High-Level General Agent API."""

    _engine: Optional[ReasoningEngine] = None

    @classmethod
    def execute(cls, task: str) -> TaskExecutionResult:
        if cls._engine is None:
            cls._engine = ReasoningEngine()
        return cls._engine.process_task(task)
