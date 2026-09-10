"""
Real-World Workflow Engine for JARVIS Orchestration.

Provides explicit workflow abstractions (DRAFT, READY, RUNNING, WAITING_FOR_USER,
WAITING_FOR_CONFIRMATION, PAUSED, RECOVERING, PARTIAL_SUCCESS, COMPLETED, FAILED, CANCELLED)
over top of the existing plan/executor orchestrator.
"""

from enum import Enum
import uuid
import time
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from jarvis.core.orchestration.plan import Plan, PlanStep, PlanStepStatus
from jarvis.core.orchestration.orchestrator import JarvisOrchestrator

logger = logging.getLogger(__name__)


class WorkflowState(str, Enum):
    DRAFT = "DRAFT"
    READY = "READY"
    RUNNING = "RUNNING"
    WAITING_FOR_USER = "WAITING_FOR_USER"
    WAITING_FOR_CONFIRMATION = "WAITING_FOR_CONFIRMATION"
    PAUSED = "PAUSED"
    RECOVERING = "RECOVERING"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class WorkflowStep(BaseModel):
    step_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    tool_name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    dependencies: List[str] = Field(default_factory=list)
    rollback_action: Optional[str] = None
    status: PlanStepStatus = PlanStepStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None


class Workflow(BaseModel):
    workflow_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    goal: str
    steps: List[WorkflowStep] = Field(default_factory=list)
    state: WorkflowState = WorkflowState.DRAFT
    context: Dict[str, Any] = Field(default_factory=dict)
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)
    progress_percentage: float = 0.0

    def update_state(self, new_state: WorkflowState) -> None:
        self.state = new_state
        self.updated_at = time.time()


class WorkflowEngine:
    """Manages multi-step daily computer-use workflow execution, state, and checkpoints."""

    def __init__(self, orchestrator: Optional[JarvisOrchestrator] = None):
        self.orchestrator = orchestrator or JarvisOrchestrator()
        self.active_workflows: Dict[str, Workflow] = {}

    def create_workflow(self, name: str, goal: str, steps: List[WorkflowStep], context: Optional[Dict[str, Any]] = None) -> Workflow:
        wf = Workflow(
            name=name,
            goal=goal,
            steps=steps,
            state=WorkflowState.READY,
            context=context or {}
        )
        self.active_workflows[wf.workflow_id] = wf
        logger.info(f"WorkflowEngine created workflow '{name}' ({wf.workflow_id}) with {len(steps)} steps.")
        return wf

    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        return self.active_workflows.get(workflow_id)

    def pause_workflow(self, workflow_id: str, reason: str = "User requested pause") -> bool:
        wf = self.get_workflow(workflow_id)
        if wf and wf.state == WorkflowState.RUNNING:
            wf.update_state(WorkflowState.PAUSED)
            wf.context["pause_reason"] = reason
            logger.info(f"Workflow '{workflow_id}' paused: {reason}")
            return True
        return False

    def resume_workflow(self, workflow_id: str) -> bool:
        wf = self.get_workflow(workflow_id)
        if wf and wf.state in (WorkflowState.PAUSED, WorkflowState.WAITING_FOR_USER):
            wf.update_state(WorkflowState.RUNNING)
            logger.info(f"Workflow '{workflow_id}' resumed.")
            return True
        return False

    def cancel_workflow(self, workflow_id: str) -> bool:
        wf = self.get_workflow(workflow_id)
        if wf and wf.state not in (WorkflowState.COMPLETED, WorkflowState.CANCELLED):
            wf.update_state(WorkflowState.CANCELLED)
            logger.info(f"Workflow '{workflow_id}' cancelled.")
            return True
        return False

    def execute_workflow(self, workflow_id: str) -> Workflow:
        wf = self.get_workflow(workflow_id)
        if not wf:
            raise ValueError(f"Workflow '{workflow_id}' not found.")

        wf.update_state(WorkflowState.RUNNING)
        completed_count = 0

        for idx, step in enumerate(wf.steps):
            if wf.state == WorkflowState.PAUSED or wf.state == WorkflowState.CANCELLED:
                break

            step.status = PlanStepStatus.EXECUTING
            # Execute step via ToolDispatcher
            result = self.orchestrator.dispatcher.dispatch(step.tool_name, step.arguments)
            if result.success:
                step.status = PlanStepStatus.COMPLETED
                step.result = result.data
                completed_count += 1
            else:
                step.status = PlanStepStatus.FAILED
                step.error = result.error
                wf.update_state(WorkflowState.RECOVERING)
                # Attempt recovery or mark partial failure
                break

            wf.progress_percentage = round((completed_count / len(wf.steps)) * 100.0, 1)

        if completed_count == len(wf.steps):
            wf.update_state(WorkflowState.COMPLETED)
        elif completed_count > 0:
            wf.update_state(WorkflowState.PARTIAL_SUCCESS)
        else:
            wf.update_state(WorkflowState.FAILED)

        return wf
