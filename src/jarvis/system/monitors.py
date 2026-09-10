"""
Governed User-Defined Condition Monitors for JARVIS.

Allows Boss to explicitly request monitored conditions ("Tell me when the download finishes",
"Watch this file") with resource budgets, permission checks, and cancellation.
"""

from enum import Enum
import uuid
import time
import logging
from typing import Dict, Any, List, Optional, Callable
from pydantic import BaseModel, Field

from jarvis.security.permissions import PermissionCategory, RiskLevel, PermissionEvaluator
from jarvis.system.notification_center import NotificationCenter, NotificationCategory

logger = logging.getLogger(__name__)
evaluator = PermissionEvaluator()


class MonitorConditionType(str, Enum):
    FILE_EXISTS = "FILE_EXISTS"
    FILE_MODIFIED = "FILE_MODIFIED"
    DOWNLOAD_COMPLETE = "DOWNLOAD_COMPLETE"
    APPLICATION_STARTED = "APPLICATION_STARTED"
    TASK_FINISHED = "TASK_FINISHED"
    CUSTOM_CHECK = "CUSTOM_CHECK"


class UserMonitor(BaseModel):
    monitor_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    owner: str = "Boss"
    name: str
    condition_type: MonitorConditionType
    target: str
    action_on_trigger: str
    created_at: float = Field(default_factory=time.time)
    expires_at: Optional[float] = None
    enabled: bool = True
    triggered: bool = False
    poll_interval_sec: float = 2.0
    max_runtime_sec: float = 3600.0
    permission_category: PermissionCategory = PermissionCategory.SYSTEM_CONTROL
    risk_level: RiskLevel = RiskLevel.LOW


class MonitorManager:
    """Manages explicit user-defined background condition monitors."""

    def __init__(self, notifier: Optional[NotificationCenter] = None):
        self.notifier = notifier or NotificationCenter.get_instance()
        self.monitors: Dict[str, UserMonitor] = {}

    def create_monitor(
        self,
        name: str,
        condition_type: MonitorConditionType,
        target: str,
        action_on_trigger: str,
        duration_sec: float = 3600.0,
        permission_category: PermissionCategory = PermissionCategory.SYSTEM_CONTROL,
        risk_level: RiskLevel = RiskLevel.LOW,
    ) -> UserMonitor:
        chk = evaluator.evaluate(category=permission_category, risk_level=risk_level, action_name=f"monitor.{condition_type.value}", parameters={"target": target})
        if not chk.allowed:
            raise PermissionError(f"Permission Denied creating monitor '{name}': {chk.reason}")

        now = time.time()
        mon = UserMonitor(
            name=name,
            condition_type=condition_type,
            target=target,
            action_on_trigger=action_on_trigger,
            created_at=now,
            expires_at=now + duration_sec,
            permission_category=permission_category,
            risk_level=risk_level
        )
        self.monitors[mon.monitor_id] = mon
        logger.info(f"MonitorManager created monitor '{name}' ({mon.monitor_id}) watching '{target}'.")
        return mon

    def cancel_monitor(self, monitor_id: str) -> bool:
        if monitor_id in self.monitors:
            self.monitors[monitor_id].enabled = False
            logger.info(f"Monitor '{monitor_id}' cancelled.")
            return True
        return False

    def list_monitors(self, active_only: bool = True) -> List[UserMonitor]:
        res = list(self.monitors.values())
        if active_only:
            now = time.time()
            res = [m for m in res if m.enabled and not m.triggered and (m.expires_at is None or m.expires_at > now)]
        return res

    def evaluate_monitors(self, check_fn: Optional[Callable[[UserMonitor], bool]] = None) -> List[UserMonitor]:
        """Evaluates active monitors against current environment state."""
        triggered_list = []
        now = time.time()

        for mon in self.list_monitors(active_only=True):
            if mon.expires_at and now > mon.expires_at:
                mon.enabled = False
                continue

            is_triggered = False
            if check_fn:
                is_triggered = check_fn(mon)

            if is_triggered:
                mon.triggered = True
                mon.enabled = False
                triggered_list.append(mon)
                self.notifier.notify(
                    category=NotificationCategory.TASK_COMPLETE,
                    title=f"Monitor Triggered: {mon.name}",
                    message=f"Condition '{mon.condition_type.value}' met for '{mon.target}'. Action: {mon.action_on_trigger}"
                )

        return triggered_list
