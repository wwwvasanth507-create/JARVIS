"""
Core Data Models for JARVIS Goal Subsystem.
"""

from enum import Enum, IntEnum
import uuid
import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from jarvis.security.permissions import RiskLevel


class GoalStatus(str, Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    BLOCKED = "BLOCKED"
    WAITING_FOR_USER = "WAITING_FOR_USER"
    AT_RISK = "AT_RISK"
    COMPLETED = "COMPLETED"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


class GoalPriority(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    NORMAL = "NORMAL"
    LOW = "LOW"

    @property
    def rank(self) -> int:
        mapping = {"CRITICAL": 4, "HIGH": 3, "NORMAL": 2, "LOW": 1}
        return mapping.get(self.value, 1)


class AutonomyLevel(IntEnum):
    LEVEL_0_MANUAL = 0
    LEVEL_1_ASSISTED = 1
    LEVEL_2_SUPERVISED = 2
    LEVEL_3_SCHEDULED = 3


class DeadlineType(str, Enum):
    NONE = "NONE"
    SOFT = "SOFT"
    HARD = "HARD"
    RECURRING = "RECURRING"


class GoalOwner(str, Enum):
    USER = "USER"
    SCHEDULED = "SCHEDULED"
    BACKGROUND_MONITOR = "BACKGROUND_MONITOR"
    SYSTEM_MAINTENANCE = "SYSTEM_MAINTENANCE"


class ProgressConfidence(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNKNOWN = "UNKNOWN"


class DeadlineRisk(str, Enum):
    ON_TRACK = "ON_TRACK"
    AT_RISK = "AT_RISK"
    OVERDUE = "OVERDUE"
    UNKNOWN = "UNKNOWN"


class ObjectiveStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    BLOCKED = "BLOCKED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class Objective(BaseModel):
    objective_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    goal_id: str
    title: str
    description: str = ""
    status: ObjectiveStatus = ObjectiveStatus.PENDING
    dependencies: List[str] = Field(default_factory=list)
    completion_criteria: List[str] = Field(default_factory=list)
    verification: Dict[str, Any] = Field(default_factory=dict)
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)


class GoalCheckpoint(BaseModel):
    checkpoint_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    goal_id: str
    state: Dict[str, Any] = Field(default_factory=dict)
    verified_outputs: List[Dict[str, Any]] = Field(default_factory=list)
    blockers: List[str] = Field(default_factory=list)
    resource_usage: Dict[str, Any] = Field(default_factory=dict)
    created_at: float = Field(default_factory=time.time)


class Goal(BaseModel):
    goal_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str = ""
    owner: GoalOwner = GoalOwner.USER
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)
    status: GoalStatus = GoalStatus.DRAFT
    priority: GoalPriority = GoalPriority.NORMAL
    deadline: Optional[float] = None
    deadline_type: DeadlineType = DeadlineType.SOFT
    time_window: Dict[str, Any] = Field(default_factory=dict)
    constraints: Dict[str, Any] = Field(default_factory=dict)
    dependencies: List[str] = Field(default_factory=list)
    success_criteria: List[str] = Field(default_factory=list)
    risk_level: RiskLevel = RiskLevel.LOW
    resource_budget: Dict[str, Any] = Field(default_factory=lambda: {"max_cpu_percent": 50, "max_ram_mb": 1024, "max_runtime_sec": 3600})
    progress: float = 0.0
    progress_confidence: ProgressConfidence = ProgressConfidence.MEDIUM
    autonomy_level: AutonomyLevel = AutonomyLevel.LEVEL_1_ASSISTED
    associated_project: Optional[str] = None
    associated_memories: List[str] = Field(default_factory=list)
    objectives: List[Objective] = Field(default_factory=list)
    blockers: List[str] = Field(default_factory=list)


class GoalTemplate(BaseModel):
    template_id: str
    name: str
    description: str
    version: str = "1.0.0"
    created_at: float = Field(default_factory=time.time)
    required_capabilities: List[str] = Field(default_factory=list)
    risk_level: RiskLevel = RiskLevel.LOW
    default_autonomy_level: AutonomyLevel = AutonomyLevel.LEVEL_1_ASSISTED
    objective_templates: List[Dict[str, Any]] = Field(default_factory=list)
    default_resource_budget: Dict[str, Any] = Field(default_factory=dict)


class GoalProgress(BaseModel):
    goal_id: str
    progress_percent: float
    confidence: ProgressConfidence
    total_objectives: int
    completed_objectives: int
    blocked_objectives: int
    current_activity: str
    deadline_risk: DeadlineRisk
    health_score: float  # 0.0 to 1.0
