"""
Unit tests for SchedulerPolicy.
"""

from jarvis.scheduler.models import ScheduledTask, TaskState
from jarvis.scheduler.policy import SchedulerPolicy
from jarvis.security.permissions import RiskLevel


def test_evaluate_runtime_permissions_allowed():
    policy = SchedulerPolicy()
    task = ScheduledTask(name="Safe Reminder", action="remind me to test", tool_name=None, risk_level=RiskLevel.LOW)
    allowed, reason, risk = policy.evaluate_task_runtime_permissions(task)
    assert allowed is True


def test_recurring_failure_threshold_check():
    policy = SchedulerPolicy()
    task = ScheduledTask(name="Failing Task", failure_count=3)
    assert policy.check_recurring_failure_limit(task) is True
