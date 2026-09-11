"""
High-Level Scheduler Manager Facade for JARVIS.
Provides unified management for creating, querying, updating, cancelling, pausing, and resuming scheduled tasks.
"""

import time
import logging
from typing import List, Optional, Dict, Any
from jarvis.scheduler.cancellation import TaskCanceller
from jarvis.scheduler.models import ScheduledTask, TaskRun, TaskState, TaskPriority
from jarvis.scheduler.notifications import NotificationManager
from jarvis.scheduler.parser import ScheduleParser
from jarvis.scheduler.persistence import TaskPersistence
from jarvis.scheduler.policy import SchedulerPolicy
from jarvis.scheduler.scheduler import TaskScheduler
from jarvis.security.permissions import RiskLevel

logger = logging.getLogger("jarvis.scheduler.manager")


class SchedulerManager:
    """Unified entry point for task scheduling and background automation."""

    def __init__(
        self,
        persistence: Optional[TaskPersistence] = None,
        parser: Optional[ScheduleParser] = None,
        policy: Optional[SchedulerPolicy] = None,
        notification_mgr: Optional[NotificationManager] = None,
        db_manager: Optional[Any] = None,
        orchestrator: Optional[Any] = None,
    ):
        self.persistence = persistence or (TaskPersistence(db_manager=db_manager) if db_manager else TaskPersistence())
        self.parser = parser or ScheduleParser()
        self.policy = policy or SchedulerPolicy()
        self.notification_mgr = notification_mgr or NotificationManager()
        self.orchestrator = orchestrator
        self.canceller = TaskCanceller(self.persistence)
        self.scheduler = TaskScheduler(self.persistence)

    def start(self) -> None:
        """Starts background scheduler."""
        self.scheduler.start()

    def stop(self) -> None:
        """Stops background scheduler."""
        self.scheduler.stop()

    def create_scheduled_task(
        self,
        name: str,
        schedule_expression: str,
        action: str = "",
        tool_name: Optional[str] = None,
        arguments: Optional[Dict[str, Any]] = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        risk_level: RiskLevel = RiskLevel.LOW,
        notification_type: str = "TEXT",
    ) -> ScheduledTask:
        """Parses schedule expression and persists new ScheduledTask."""
        next_run, is_rec, norm_expr = self.parser.parse_expression(schedule_expression)

        task = ScheduledTask(
            name=name,
            action=action or name,
            tool_name=tool_name,
            arguments=arguments or {},
            schedule=norm_expr,
            next_run_at=next_run,
            is_recurring=is_rec,
            priority=priority,
            risk_level=risk_level,
            notification_type=notification_type,
            status=TaskState.SCHEDULED,
        )

        self.persistence.save_task(task)
        self.scheduler.wake()
        logger.info(f"Created scheduled task '{task.name}' (id: {task.task_id}, next_run: {task.next_run_at})")
        return task

    def get_task(self, task_id: str) -> Optional[ScheduledTask]:
        return self.persistence.get_task(task_id)

    def list_tasks(self, include_disabled: bool = False) -> List[ScheduledTask]:
        return self.persistence.list_tasks(include_disabled=include_disabled)

    def update_task(self, task_id: str, updates: Dict[str, Any]) -> Optional[ScheduledTask]:
        task = self.persistence.get_task(task_id)
        if not task:
            return None

        for k, v in updates.items():
            if hasattr(task, k) and v is not None:
                setattr(task, k, v)

        task.updated_at = time.time()
        self.persistence.save_task(task)
        self.scheduler.wake()
        return task

    def pause_task(self, task_id: str) -> bool:
        task = self.persistence.get_task(task_id)
        if not task:
            return False
        task.status = TaskState.PAUSED
        task.updated_at = time.time()
        self.persistence.save_task(task)
        self.scheduler.wake()
        return True

    def resume_task(self, task_id: str) -> bool:
        task = self.persistence.get_task(task_id)
        if not task:
            return False
        task.status = TaskState.SCHEDULED
        task.failure_count = 0
        task.next_run_at = self.parser.parse_expression(task.schedule)[0]
        task.updated_at = time.time()
        self.persistence.save_task(task)
        self.scheduler.wake()
        return True

    def cancel_task(self, task_id: str) -> bool:
        res = self.canceller.cancel_scheduled_task(task_id)
        if res:
            self.scheduler.wake()
        return res

    def delete_task(self, task_id: str) -> bool:
        res = self.persistence.delete_task(task_id)
        if res:
            self.scheduler.wake()
        return res

    def list_history(self, task_id: Optional[str] = None, limit: int = 50) -> List[TaskRun]:
        return self.persistence.list_runs(task_id=task_id, limit=limit)

    def get_status(self) -> Dict[str, Any]:
        tasks = self.persistence.list_tasks(include_disabled=True)
        return {
            "running": self.scheduler.is_running,
            "total_tasks": len(tasks),
            "scheduled_tasks": sum(1 for t in tasks if t.status == TaskState.SCHEDULED),
            "paused_tasks": sum(1 for t in tasks if t.status == TaskState.PAUSED),
            "failed_tasks": sum(1 for t in tasks if t.status == TaskState.FAILED),
        }
