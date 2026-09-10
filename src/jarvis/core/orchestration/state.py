"""
Execution state representations for JARVIS orchestration.
"""

from enum import Enum
from time import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ExecutionStatus(str, Enum):
    PLANNING = "PLANNING"
    WAITING_FOR_CONFIRMATION = "WAITING_FOR_CONFIRMATION"
    EXECUTING = "EXECUTING"
    VERIFYING = "VERIFYING"
    RECOVERING = "RECOVERING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    NEEDS_CLARIFICATION = "NEEDS_CLARIFICATION"


class ExecutionHistoryEntry(BaseModel):
    execution_id: str
    request: str
    intent_action: Optional[str] = None
    goal_description: Optional[str] = None
    status: ExecutionStatus
    steps_total: int = 0
    steps_completed: int = 0
    duration_ms: float = 0.0
    timestamp: float = Field(default_factory=time)
    verified: bool = False
    error: Optional[str] = None


class ExecutionState(BaseModel):
    execution_id: str
    request: str
    status: ExecutionStatus = ExecutionStatus.PLANNING
    goal: Optional[Any] = None
    plan: Optional[Any] = None
    current_step: Optional[Any] = None
    completed_steps: List[Any] = Field(default_factory=list)
    failed_steps: List[Any] = Field(default_factory=list)
    pending_steps: List[Any] = Field(default_factory=list)
    observations: List[Dict[str, Any]] = Field(default_factory=list)
    verification_results: List[Dict[str, Any]] = Field(default_factory=list)
    start_time: float = Field(default_factory=time)
    end_time: Optional[float] = None
    confirmation_token: Optional[str] = None
    error: Optional[str] = None
    fast_path_used: bool = False

    @property
    def is_terminal(self) -> bool:
        return self.status in (
            ExecutionStatus.COMPLETED,
            ExecutionStatus.FAILED,
            ExecutionStatus.CANCELLED,
        )
