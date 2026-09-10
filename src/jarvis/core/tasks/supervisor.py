"""
Supervisor Engine for Long-Running Tasks in JARVIS.

Periodically evaluates active long-running tasks, performs lightweight checks,
transitions stalled tasks to DEGRADED or RECOVERING, and reconciles orphan tasks post-restart.
"""

import time
import logging
from typing import Dict, Any, List, Optional

from jarvis.core.tasks.task_manager import LongRunningTaskManager, LongRunningTask, TaskStatus
from jarvis.core.tasks.stall_detector import StallDetector
from jarvis.system.notification_center import NotificationCenter, NotificationCategory

logger = logging.getLogger(__name__)


class TaskSupervisorEngine:
    """Governed periodic supervisor engine for long-running computer-use tasks."""

    def __init__(
        self,
        task_manager: Optional[LongRunningTaskManager] = None,
        stall_detector: Optional[StallDetector] = None,
        notifier: Optional[NotificationCenter] = None,
    ):
        self.task_manager = task_manager or LongRunningTaskManager.get_instance()
        self.stall_detector = stall_detector or StallDetector(self.task_manager)
        self.notifier = notifier or NotificationCenter.get_instance()
        self.last_supervisor_run: float = 0.0

    def run_supervisor_cycle(self) -> Dict[str, Any]:
        """Executes one lightweight supervisory cycle over active tasks."""
        self.last_supervisor_run = time.time()
        stalled_tasks = self.stall_detector.scan_for_stalled_tasks()
        degraded_count = 0
        recovering_count = 0

        for task, reason in stalled_tasks:
            if task.failure_count < 2:
                task.status = TaskStatus.RECOVERING
                task.failure_count += 1
                recovering_count += 1
                logger.info(f"Supervisor transitioning task '{task.task_id}' -> RECOVERING (Reason: {reason})")
            else:
                task.status = TaskStatus.DEGRADED
                degraded_count += 1
                logger.warning(f"Supervisor transitioning task '{task.task_id}' -> DEGRADED (Reason: {reason})")
                self.notifier.notify(
                    category=NotificationCategory.SYSTEM_WARNING,
                    title="Task Stalled",
                    message=f"Task '{task.goal}' has degraded: {reason}",
                    task_id=task.task_id
                )

        return {
            "cycle_time": self.last_supervisor_run,
            "stalled_count": len(stalled_tasks),
            "recovering_count": recovering_count,
            "degraded_count": degraded_count,
        }

    def reconcile_orphan_tasks_on_startup(self) -> List[LongRunningTask]:
        """Reconciles interrupted/running tasks left behind post-crash or restart."""
        reconciled = []
        for task in self.task_manager.list_tasks():
            if task.status == TaskStatus.RUNNING:
                task.status = TaskStatus.PAUSED
                task.context["orphan_reconciled"] = True
                reconciled.append(task)
                logger.info(f"Startup reconciliation paused orphaned running task '{task.task_id}'")
        return reconciled
