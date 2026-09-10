"""
Stall Detector for Long-Running Tasks in JARVIS.

Detects frozen browser sessions, unresponsive desktop applications, un-progressing workflows,
and missing workers.
"""

import time
import logging
from typing import Dict, Any, List, Optional, Tuple

from jarvis.core.tasks.task_manager import LongRunningTaskManager, LongRunningTask, TaskStatus

logger = logging.getLogger(__name__)


class StallDetector:
    """Evaluates task progress and detects stalled or frozen tasks."""

    def __init__(self, task_manager: Optional[LongRunningTaskManager] = None, stall_threshold_sec: float = 300.0):
        self.task_manager = task_manager or LongRunningTaskManager.get_instance()
        self.stall_threshold_sec = stall_threshold_sec

    def check_task_stall(self, task: LongRunningTask) -> Tuple[bool, str]:
        """Checks if a single running task is stalled."""
        if task.status not in (TaskStatus.RUNNING, TaskStatus.RECOVERING):
            return False, "Task not running"

        now = time.time()
        elapsed_since_progress = now - task.heartbeat.last_progress_time

        # 1. Heartbeat progress timeout
        if elapsed_since_progress > self.stall_threshold_sec:
            msg = f"Task progress stalled for {round(elapsed_since_progress, 1)}s (threshold={self.stall_threshold_sec}s)"
            logger.warning(f"StallDetector: {msg} on task {task.task_id}")
            return True, msg

        # 2. Expired lease check for active running tasks
        if task.status == TaskStatus.RUNNING and task.lease_owner and not task.is_lease_valid():
            msg = f"Task worker lease expired for '{task.lease_owner}'"
            logger.warning(f"StallDetector: {msg} on task {task.task_id}")
            return True, msg

        return False, "Healthy"

    def scan_for_stalled_tasks(self) -> List[Tuple[LongRunningTask, str]]:
        """Scans all active tasks and returns list of stalled tasks with reasons."""
        stalled = []
        for task in self.task_manager.list_tasks():
            is_stalled, reason = self.check_task_stall(task)
            if is_stalled:
                stalled.append((task, reason))
        return stalled
