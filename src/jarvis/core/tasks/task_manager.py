"""
Governed Long-Running Task Manager & Heartbeat Subsystem for JARVIS.

Tracks long-running tasks across 13 statuses (CREATED, QUEUED, RUNNING, WAITING_FOR_USER,
WAITING_FOR_CONFIRMATION, PAUSED, RECOVERING, DEGRADED, COMPLETED, PARTIAL_SUCCESS, FAILED, CANCELLED, EXPIRED),
environment fingerprints, task heartbeats, task leases, and idempotency protection.
"""

from enum import Enum
import uuid
import time
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from jarvis.security.permissions import PermissionCategory, RiskLevel

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    CREATED = "CREATED"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    WAITING_FOR_USER = "WAITING_FOR_USER"
    WAITING_FOR_CONFIRMATION = "WAITING_FOR_CONFIRMATION"
    PAUSED = "PAUSED"
    RECOVERING = "RECOVERING"
    DEGRADED = "DEGRADED"
    COMPLETED = "COMPLETED"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


class EnvironmentFingerprint(BaseModel):
    active_application: Optional[str] = None
    window_title: Optional[str] = None
    target_file_exists: bool = False
    network_available: bool = True
    model_available: bool = True
    timestamp: float = Field(default_factory=time.time)


class TaskHeartbeat(BaseModel):
    last_progress_time: float = Field(default_factory=time.time)
    last_state_change: float = Field(default_factory=time.time)
    last_tool_call: Optional[str] = None
    last_verification_success: bool = True
    heartbeat_status: str = "HEALTHY"


class LongRunningTask(BaseModel):
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    goal: str
    owner: str = "Boss"
    priority: int = 1  # 1 = Normal, 2 = High
    created_at: float = Field(default_factory=time.time)
    started_at: Optional[float] = None
    status: TaskStatus = TaskStatus.CREATED
    current_step_index: int = 0
    total_steps: int = 1
    context: Dict[str, Any] = Field(default_factory=dict)
    resource_budget: Dict[str, Any] = Field(default_factory=lambda: {"max_runtime_sec": 3600, "max_tool_calls": 50})
    permission_category: PermissionCategory = PermissionCategory.SYSTEM_CONTROL
    risk_level: RiskLevel = RiskLevel.LOW
    environment_fingerprint: Optional[EnvironmentFingerprint] = None
    heartbeat: TaskHeartbeat = Field(default_factory=TaskHeartbeat)
    failure_count: int = 0
    recovery_count: int = 0
    idempotency_key: Optional[str] = None
    lease_owner: Optional[str] = None
    lease_expires_at: Optional[float] = None

    def update_heartbeat(self, tool_name: Optional[str] = None, verification_success: bool = True) -> None:
        now = time.time()
        self.heartbeat.last_progress_time = now
        if tool_name:
            self.heartbeat.last_tool_call = tool_name
        self.heartbeat.last_verification_success = verification_success
        self.heartbeat.heartbeat_status = "HEALTHY"

    def is_lease_valid(self) -> bool:
        if not self.lease_expires_at:
            return False
        return time.time() < self.lease_expires_at


class LongRunningTaskManager:
    """Manager providing lifecycle control and leasing for long-running computer-use tasks."""

    _instance: Optional["LongRunningTaskManager"] = None

    def __init__(self):
        self.tasks: Dict[str, LongRunningTask] = {}
        self.idempotency_store: Dict[str, str] = {}  # key -> task_id

    @classmethod
    def get_instance(cls) -> "LongRunningTaskManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def create_task(self, goal: str, total_steps: int = 1, idempotency_key: Optional[str] = None, context: Optional[Dict[str, Any]] = None) -> LongRunningTask:
        if idempotency_key and idempotency_key in self.idempotency_store:
            existing_id = self.idempotency_store[idempotency_key]
            logger.info(f"Duplicate task creation prevented by idempotency key '{idempotency_key}' (Task {existing_id}).")
            return self.tasks[existing_id]

        task = LongRunningTask(
            goal=goal,
            total_steps=total_steps,
            idempotency_key=idempotency_key,
            context=context or {}
        )
        self.tasks[task.task_id] = task
        if idempotency_key:
            self.idempotency_store[idempotency_key] = task.task_id

        logger.info(f"LongRunningTaskManager created task '{task.task_id}': {goal}")
        return task

    def acquire_lease(self, task_id: str, worker_id: str, lease_duration_sec: float = 30.0) -> bool:
        task = self.tasks.get(task_id)
        if not task:
            return False
        now = time.time()
        if task.lease_owner and task.is_lease_valid() and task.lease_owner != worker_id:
            logger.warning(f"Task lease acquisition failed for {task_id}: owned by {task.lease_owner}")
            return False
        task.lease_owner = worker_id
        task.lease_expires_at = now + lease_duration_sec
        return True

    def update_task_status(self, task_id: str, status: TaskStatus) -> Optional[LongRunningTask]:
        task = self.tasks.get(task_id)
        if task:
            task.status = status
            task.heartbeat.last_state_change = time.time()
            logger.info(f"Task '{task_id}' status updated -> {status.value}")
        return task

    def list_tasks(self, status: Optional[TaskStatus] = None) -> List[LongRunningTask]:
        if status is None:
            return list(self.tasks.values())
        return [t for t in self.tasks.values() if t.status == status]
