"""
Recovery Integration for JARVIS Scheduler.
Integrates Prompt 015 JarvisRecoveryManager into scheduled task failure workflows.
"""

import logging
from typing import Optional, Dict, Any, Tuple
from jarvis.core.recovery.recovery import JarvisRecoveryManager
from jarvis.core.recovery.planner import RecoveryPlan
from jarvis.core.recovery.root_cause import RootCause
from jarvis.scheduler.models import ScheduledTask, TaskRun

logger = logging.getLogger("jarvis.scheduler.recovery")


class SchedulerRecovery:
    """Invokes Prompt 015 diagnostic self-recovery on scheduled task failures."""

    def __init__(self, recovery_manager: Optional[JarvisRecoveryManager] = None):
        self.recovery_manager = recovery_manager or JarvisRecoveryManager()

    def handle_task_failure(
        self,
        task: ScheduledTask,
        run: TaskRun,
        error_message: str
    ) -> Tuple[bool, Optional[RecoveryPlan], Optional[RootCause]]:
        """
        Runs diagnostic self-recovery on a scheduled task execution failure.
        """
        tool_name = task.tool_name or task.action or "system.status"
        return self.recovery_manager.handle_failure(
            execution_id=run.run_id,
            step_id=f"step_{task.task_id}",
            tool_name=tool_name,
            arguments=task.arguments,
            error_message=error_message,
            retry_count=task.failure_count,
        )
