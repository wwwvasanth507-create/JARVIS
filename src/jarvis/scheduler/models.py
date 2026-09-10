"""
Pydantic data models for JARVIS Scheduler.
"""

import time
import uuid
from datetime import datetime, timezone
from enum import Enum, IntEnum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from jarvis.security.permissions import RiskLevel


class TaskPriority(IntEnum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class TaskState(str, Enum):
    SCHEDULED = "SCHEDULED"
    READY = "READY"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    PAUSED = "PAUSED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"
    WAITING_FOR_CONFIRMATION = "WAITING_FOR_CONFIRMATION"
    BLOCKED = "BLOCKED"


class ScheduledTask(BaseModel):
    """Data model representing a scheduled task definition."""

    task_id: str = Field(default_factory=lambda: f"task_{uuid.uuid4().hex[:12]}")
    name: str
    description: str = ""
    action: str = ""
    skill_id: Optional[str] = None
    tool_name: Optional[str] = None
    arguments: Dict[str, Any] = Field(default_factory=dict)
    schedule: str = ""  # Natural language or recurrence pattern
    timezone: str = "UTC"
    status: TaskState = TaskState.SCHEDULED
    priority: TaskPriority = TaskPriority.NORMAL
    risk_level: RiskLevel = RiskLevel.LOW
    enabled: bool = True
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)
    next_run_at: Optional[float] = None
    last_run_at: Optional[float] = None
    last_result: Optional[Dict[str, Any]] = None
    failure_count: int = 0
    is_recurring: bool = False
    notification_type: str = "TEXT"  # TEXT, DESKTOP, VOICE


class TaskRun(BaseModel):
    """Data model representing an individual execution instance of a task."""

    run_id: str = Field(default_factory=lambda: f"run_{uuid.uuid4().hex[:12]}")
    task_id: str
    started_at: float = Field(default_factory=time.time)
    finished_at: Optional[float] = None
    status: TaskState = TaskState.RUNNING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    verification_result: Optional[Dict[str, Any]] = None
    recovery_attempts: int = 0
