"""
Task Executor for JARVIS Scheduler.
Mandatory execution path: Scheduler -> Orchestrator -> Intent/Plan -> Permission -> Execution -> Verification.
"""

import time
import logging
from typing import Optional, Dict, Any
from jarvis.scheduler.models import ScheduledTask, TaskRun, TaskState
from jarvis.scheduler.notifications import NotificationManager
from jarvis.scheduler.policy import SchedulerPolicy
from jarvis.scheduler.recovery import SchedulerRecovery

logger = logging.getLogger("jarvis.scheduler.executor")


class TaskExecutor:
    """Executes scheduled tasks through JarvisOrchestrator."""

    def __init__(
        self,
        orchestrator: Optional[Any] = None,
        policy: Optional[SchedulerPolicy] = None,
        notification_mgr: Optional[NotificationManager] = None,
        scheduler_recovery: Optional[SchedulerRecovery] = None,
    ):
        self._orchestrator = orchestrator
        self.policy = policy or SchedulerPolicy()
        self.notification_mgr = notification_mgr or NotificationManager()
        self.scheduler_recovery = scheduler_recovery or SchedulerRecovery()

    @property
    def orchestrator(self) -> Any:
        if self._orchestrator is None:
            from jarvis.core.orchestration.orchestrator import JarvisOrchestrator
            self._orchestrator = JarvisOrchestrator()
        return self._orchestrator

    def execute_scheduled_task(self, task: ScheduledTask) -> TaskRun:
        """
        Executes a scheduled task through the orchestrator.
        """
        run = TaskRun(task_id=task.task_id, started_at=time.time())

        # 1. Runtime permission check
        allowed, reason, risk = self.policy.evaluate_task_runtime_permissions(task)
        if not allowed:
            run.finished_at = time.time()
            run.status = TaskState.BLOCKED
            run.error = reason or "Runtime permission check failed"
            return run

        # 2. Check if simple notification/reminder
        if task.action and not task.tool_name and not task.skill_id and "remind" in task.action.lower():
            sent = self.notification_mgr.notify(
                message=task.name or task.action,
                notification_type=task.notification_type,
                title="JARVIS Scheduled Reminder",
            )
            run.finished_at = time.time()
            run.status = TaskState.COMPLETED if sent else TaskState.FAILED
            run.result = {"notification_sent": sent}
            return run

        # 3. Execution via JarvisOrchestrator
        from jarvis.core.orchestration.state import ExecutionStatus
        req_str = task.action or f"Execute scheduled task {task.name}"
        try:
            exec_state = self.orchestrator.handle(req_str)

            run.finished_at = time.time()
            if exec_state.status == ExecutionStatus.COMPLETED:
                run.status = TaskState.COMPLETED
                run.result = {"execution_id": exec_state.execution_id, "observations": exec_state.observations}
            elif exec_state.status == ExecutionStatus.WAITING_FOR_CONFIRMATION:
                run.status = TaskState.WAITING_FOR_CONFIRMATION
                run.error = "Confirmation required for execution"
            else:
                run.status = TaskState.FAILED
                run.error = exec_state.error or "Orchestrator execution failed"
        except Exception as err:
            run.finished_at = time.time()
            run.status = TaskState.FAILED
            run.error = str(err)

            # Attempt Prompt 015 recovery
            try:
                can_rec, plan, rc = self.scheduler_recovery.handle_task_failure(task, run, run.error)
                if can_rec and plan:
                    run.recovery_attempts += 1
            except Exception as rec_err:
                logger.warning(f"Scheduler recovery attempt failed: {rec_err}")

        return run
