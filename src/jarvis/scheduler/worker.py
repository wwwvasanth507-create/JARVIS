"""
Task Worker Pool for JARVIS Scheduler.
Executes due tasks asynchronously without blocking the main scheduler loop.
"""

import time
import threading
import logging
from typing import Optional, Dict, Any, Callable
from jarvis.scheduler.executor import TaskExecutor
from jarvis.scheduler.models import ScheduledTask, TaskRun, TaskState
from jarvis.scheduler.persistence import TaskPersistence
from jarvis.scheduler.policy import SchedulerPolicy

logger = logging.getLogger("jarvis.scheduler.worker")


class TaskWorkerPool:
    """Worker pool executing due tasks asynchronously."""

    def __init__(
        self,
        persistence: TaskPersistence,
        executor: Optional[TaskExecutor] = None,
        policy: Optional[SchedulerPolicy] = None,
        max_workers: int = 2,
    ):
        self.persistence = persistence
        self.executor = executor or TaskExecutor()
        self.policy = policy or SchedulerPolicy()
        self.max_workers = max_workers
        self.active_runs: Dict[str, TaskRun] = {}
        self._lock = threading.Lock()

    def submit(self, task: ScheduledTask, on_complete: Optional[Callable[[ScheduledTask, TaskRun], None]] = None) -> bool:
        """Submits a task for asynchronous background execution."""
        with self._lock:
            if len(self.active_runs) >= self.max_workers:
                logger.warning(f"Worker pool max capacity ({self.max_workers}) reached. Skipping submit for task '{task.task_id}'.")
                return False

            t = threading.Thread(target=self._run_task_thread, args=(task, on_complete), daemon=True)
            t.start()
            return True

    def _run_task_thread(self, task: ScheduledTask, on_complete: Optional[Callable[[ScheduledTask, TaskRun], None]]) -> None:
        task.status = TaskState.RUNNING
        task.last_run_at = time.time()
        self.persistence.save_task(task)

        run = self.executor.execute_scheduled_task(task)

        # Update task status based on run result
        if run.status == TaskState.COMPLETED:
            if not task.is_recurring:
                task.status = TaskState.COMPLETED
                task.enabled = False
            else:
                task.status = TaskState.SCHEDULED
            task.failure_count = 0
            task.last_result = run.result
        else:
            task.failure_count += 1
            if self.policy.check_recurring_failure_limit(task):
                task.status = TaskState.PAUSED
                logger.warning(f"Task '{task.name}' auto-paused after {task.failure_count} consecutive failures.")
            else:
                task.status = TaskState.FAILED if not task.is_recurring else TaskState.SCHEDULED

        task.updated_at = time.time()
        self.persistence.save_task(task)
        self.persistence.save_run(run)

        with self._lock:
            self.active_runs.pop(task.task_id, None)

        if on_complete:
            try:
                on_complete(task, run)
            except Exception as e:
                logger.warning(f"Error in task completion callback: {e}")
