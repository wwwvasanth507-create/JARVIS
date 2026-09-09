"""
Task Queue Subsystem for JARVIS.
Optimized with heapq for O(log N) insertion and fast priority popping.
"""

from datetime import datetime
from enum import Enum, IntEnum
import heapq
import itertools
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class TaskPriority(IntEnum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class TaskStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class TaskItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    payload: Dict[str, Any] = Field(default_factory=dict)
    result: Optional[Any] = None
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    cancelled: bool = False


class TaskQueue:
    """In-memory prioritized task queue for JARVIS operations."""

    def __init__(self):
        # Heap stored as tuple: (-priority_value, sequence_counter, TaskItem)
        self._heap: List[tuple] = []
        self._counter = itertools.count()
        self._task_map: Dict[str, TaskItem] = {}

    def enqueue(self, name: str, payload: Optional[Dict[str, Any]] = None, priority: TaskPriority = TaskPriority.NORMAL) -> TaskItem:
        task = TaskItem(name=name, payload=payload or {}, priority=priority)
        count = next(self._counter)
        # Higher priority value goes first (-priority for min-heap)
        heapq.heappush(self._heap, (-int(priority), count, task))
        self._task_map[task.id] = task
        return task

    def pop_next(self) -> Optional[TaskItem]:
        while self._heap:
            _, _, task = heapq.heappop(self._heap)
            if task.status == TaskStatus.PENDING and not task.cancelled:
                task.status = TaskStatus.RUNNING
                task.started_at = datetime.now()
                return task
        return None

    def cancel(self, task_id: str) -> bool:
        task = self._task_map.get(task_id)
        if task and task.status in (TaskStatus.PENDING, TaskStatus.RUNNING):
            task.cancelled = True
            task.status = TaskStatus.CANCELLED
            task.completed_at = datetime.now()
            return True
        return False

    def mark_completed(self, task_id: str, result: Optional[Any] = None) -> bool:
        task = self._task_map.get(task_id)
        if task:
            task.status = TaskStatus.COMPLETED
            task.result = result
            task.completed_at = datetime.now()
            return True
        return False

    def mark_failed(self, task_id: str, error: str) -> bool:
        task = self._task_map.get(task_id)
        if task:
            task.status = TaskStatus.FAILED
            task.error = error
            task.completed_at = datetime.now()
            return True
        return False

    @property
    def pending_count(self) -> int:
        return sum(1 for t in self._task_map.values() if t.status == TaskStatus.PENDING and not t.cancelled)
