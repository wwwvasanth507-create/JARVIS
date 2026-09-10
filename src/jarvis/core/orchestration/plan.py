"""
Plan and PlanStep data structures for JARVIS orchestration.
"""

import uuid
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from jarvis.security.permissions import PermissionCategory, RiskLevel


class PlanStepStatus(str, Enum):
    PENDING = "PENDING"
    WAITING_FOR_CONFIRMATION = "WAITING_FOR_CONFIRMATION"
    EXECUTING = "EXECUTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    SKIPPED = "SKIPPED"


class PlanStep(BaseModel):
    step_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    description: str
    tool_name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    dependencies: List[str] = Field(default_factory=list)
    risk_level: RiskLevel = RiskLevel.LOW
    permission: PermissionCategory = PermissionCategory.SYSTEM_CONTROL
    success_condition: str = "execution_succeeded"
    retry_policy: Dict[str, Any] = Field(default_factory=lambda: {"max_retries": 1, "retry_count": 0})
    status: PlanStepStatus = PlanStepStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None


class Plan(BaseModel):
    plan_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    goal_id: str
    steps: List[PlanStep] = Field(default_factory=list)
    dependencies: Dict[str, List[str]] = Field(default_factory=dict)
    status: str = "CREATED"

    def get_step(self, step_id: str) -> Optional[PlanStep]:
        for step in self.steps:
            if step.step_id == step_id:
                return step
        return None

    def get_ready_steps(self) -> List[PlanStep]:
        completed_ids = {s.step_id for s in self.steps if s.status == PlanStepStatus.COMPLETED}
        ready = []
        for step in self.steps:
            if step.status == PlanStepStatus.PENDING:
                deps_met = all(dep_id in completed_ids for dep_id in step.dependencies)
                if deps_met:
                    ready.append(step)
        return ready
