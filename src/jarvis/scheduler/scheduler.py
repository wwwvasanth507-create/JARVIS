"""
Lightweight Event-Driven Background Scheduler for JARVIS.
Uses a condition wait until next due task timestamp, consuming negligible CPU when idle.
"""

import time
import threading
import logging
from typing import Optional, List, Callable
from jarvis.scheduler.models import ScheduledTask, TaskState
from jarvis.scheduler.persistence import TaskPersistence
from jarvis.scheduler.recurrence import RecurrencePattern
from jarvis.scheduler.worker import TaskWorkerPool

logger = logging.getLogger("jarvis.scheduler.scheduler")


class TaskScheduler:
    """
    Event-driven background task scheduler thread.
    Calculates exact delay to next_run_at and sleeps on threading.Event until due.
    """

    def __init__(self, persistence: TaskPersistence, worker_pool: Optional[TaskWorkerPool] = None):
        self.persistence = persistence
        self.worker_pool = worker_pool or TaskWorkerPool(persistence=persistence)
        self._stop_event = threading.Event()
        self._wake_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self.is_running = False

    def start(self) -> None:
        """Starts the background scheduler thread."""
        if self.is_running:
            return
        self._stop_event.clear()
        self._wake_event.clear()
        self.is_running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.info("JARVIS TaskScheduler started.")

    def stop(self) -> None:
        """Stops the background scheduler thread cleanly."""
        if not self.is_running:
            return
        self.is_running = False
        self._stop_event.set()
        self._wake_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        logger.info("JARVIS TaskScheduler stopped.")

    def wake(self) -> None:
        """Signals the scheduler to re-evaluate due tasks immediately."""
        self._wake_event.set()

    def _run_loop(self) -> None:
        """Main event-driven loop."""
        while not self._stop_event.is_set():
            self._wake_event.clear()
            now_ts = time.time()

            # 1. Load active tasks
            tasks = self.persistence.list_tasks(include_disabled=False)

            due_tasks: List[ScheduledTask] = []
            next_wake_delay: float = 3600.0  # Default 1 hour sleep if no tasks scheduled

            for task in tasks:
                if task.status in (TaskState.PAUSED, TaskState.CANCELLED, TaskState.BLOCKED):
                    continue

                if not task.next_run_at:
                    task.next_run_at = RecurrencePattern.calculate_next_run(task.schedule, from_timestamp=now_ts)
                    self.persistence.save_task(task)

                if task.next_run_at and task.next_run_at <= now_ts:
                    due_tasks.append(task)
                elif task.next_run_at:
                    delay = max(0.1, task.next_run_at - now_ts)
                    next_wake_delay = min(next_wake_delay, delay)

            # 2. Dispatch due tasks
            for task in due_tasks:
                self.worker_pool.submit(task, on_complete=self._on_task_complete)

            # 3. Wait until next task is due or wake event is triggered
            self._wake_event.wait(timeout=max(0.1, next_wake_delay))

    def _on_task_complete(self, task: ScheduledTask, run: Any) -> None:
        """Callback when background worker finishes a task."""
        if task.is_recurring and task.status != TaskState.PAUSED:
            task.next_run_at = RecurrencePattern.calculate_next_run(task.schedule, from_timestamp=time.time())
            self.persistence.save_task(task)
        self.wake()
