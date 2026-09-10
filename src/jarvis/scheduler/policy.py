"""
Scheduler Security and Execution Policy Manager for JARVIS.
Enforces runtime permissions, risk escalation, missed-task policies, overlap policies, and failure thresholds.
"""

import logging
from typing import Optional, Tuple, Dict, Any
from jarvis.scheduler.errors import SchedulerPermissionDeniedError, TaskOverlapError
from jarvis.scheduler.models import ScheduledTask, TaskRun, TaskState
from jarvis.security.permissions import PermissionEvaluator, RiskLevel, PermissionCategory

logger = logging.getLogger("jarvis.scheduler.policy")


class SchedulerPolicy:
    """Evaluates security, permissions, overlap, missed tasks, and failure thresholds."""

    def __init__(self, permission_evaluator: Optional[PermissionEvaluator] = None):
        self.permission_evaluator = permission_evaluator or PermissionEvaluator()
        self.missed_task_policy = "skip"
        self.overlap_policy = "skip"
        self.recurring_failure_threshold = 3

    def evaluate_task_runtime_permissions(
        self,
        task: ScheduledTask,
        active_runs: Optional[Dict[str, TaskRun]] = None
    ) -> Tuple[bool, Optional[str], RiskLevel]:
        """
        Evaluates permissions at runtime.
        Returns (is_allowed, reason, effective_risk_level).
        """
        # 1. Overlap Check
        if active_runs and task.task_id in active_runs:
            if self.overlap_policy == "skip":
                return False, f"Task '{task.name}' is already running (overlap_policy=skip)", task.risk_level

        # 2. Map tool category
        tool_name = task.tool_name or (task.action if "." in task.action else "system.status")
        cat = PermissionCategory.COMPUTER_CONTROL
        if "screen" in tool_name or "vision" in tool_name:
            cat = PermissionCategory.SCREEN_READ
        elif "filesystem" in tool_name or "file" in tool_name:
            cat = PermissionCategory.READ_FILES if ("read" in tool_name or "find" in tool_name) else PermissionCategory.WRITE_FILES
        elif "browser" in tool_name:
            cat = PermissionCategory.BROWSER_CONTROL
        elif "application" in tool_name or "app" in tool_name:
            cat = PermissionCategory.APPLICATION_CONTROL
        elif "shell" in tool_name:
            cat = PermissionCategory.RUN_COMMANDS

        # 3. Evaluate Permission
        decision = self.permission_evaluator.evaluate(
            category=cat,
            risk_level=task.risk_level,
            action_name=tool_name,
            parameters=task.arguments,
        )

        if not decision.allowed:
            return False, f"Runtime permission check denied for tool '{tool_name}': {decision.reason}", decision.risk_level

        return True, None, decision.risk_level

    def check_recurring_failure_limit(self, task: ScheduledTask) -> bool:
        """
        Returns True if task should be auto-paused due to consecutive failures.
        """
        return task.failure_count >= self.recurring_failure_threshold
