"""
Bounded Queue Manager for JARVIS Scheduler.
Prevents unlimited background tasks and memory bloat.
"""

from typing import List, Optional
from jarvis.scheduler.models import ScheduledTask, TaskPriority


class BoundedSchedulerQueue:
    """Bounded task queue enforcing max concurrency and queue size limits."""

    def __init__(self, max_concurrent: int = 2, max_queue_size: int = 50):
        self.max_concurrent = max_concurrent
        self.max_queue_size = max_queue_size
        self._queue: List[ScheduledTask] = []

    def enqueue(self, task: ScheduledTask) -> bool:
        if len(self._queue) >= self.max_queue_size:
            return False
        self._queue.append(task)
        # Sort by priority descending, then next_run_at ascending
        self._queue.sort(key=lambda t: (-int(t.priority), t.next_run_at or 0))
        return True

    def pop_next(self) -> Optional[ScheduledTask]:
        if self._queue:
            return self._queue.pop(0)
        return None

    def clear(self) -> None:
        self._queue.clear()

    @property
    def size(self) -> int:
        return len(self._queue)
