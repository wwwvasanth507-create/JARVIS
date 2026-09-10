"""
Task Canceller for JARVIS Scheduler.
Handles graceful cancellation of pending, queued, and running scheduled tasks.
"""

import logging
from typing import Optional
from jarvis.core.orchestration.cancellation import CancellationManager
from jarvis.scheduler.models import ScheduledTask, TaskRun, TaskState
from jarvis.scheduler.persistence import TaskPersistence

logger = logging.getLogger("jarvis.scheduler.cancellation")


class TaskCanceller:
    """Manages task cancellation across queued and active task runs."""

    def __init__(self, persistence: TaskPersistence, cancellation_mgr: Optional[CancellationManager] = None):
        self.persistence = persistence
        self.cancellation_mgr = cancellation_mgr or CancellationManager()

    def cancel_scheduled_task(self, task_id: str, reason: str = "User cancelled task") -> bool:
        """Cancels a scheduled task definition and sets status to CANCELLED."""
        task = self.persistence.get_task(task_id)
        if not task:
            return False

        task.status = TaskState.CANCELLED
        task.enabled = False
        self.persistence.save_task(task)
        logger.info(f"Task '{task_id}' cancelled: {reason}")
        return True
