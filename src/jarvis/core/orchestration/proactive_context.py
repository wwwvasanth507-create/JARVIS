"""
Conservative Proactive Context Engine for JARVIS.

Surfaces requested background updates, scheduled reminders, and task failure alerts
without spontaneously performing unauthorized or risky actions.
"""

import time
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from jarvis.system.notification_center import NotificationCenter, NotificationCategory

logger = logging.getLogger(__name__)


class ProactiveContextItem(BaseModel):
    id: str
    source: str
    summary: str
    requires_user_attention: bool = False
    timestamp: float = Field(default_factory=time.time)


class ProactiveContextEngine:
    """Surfaces conservative proactive updates (reminders, failed background tasks)."""

    def __init__(self, notification_center: Optional[NotificationCenter] = None):
        self.notifier = notification_center or NotificationCenter.get_instance()
        self.proactive_items: List[ProactiveContextItem] = []

    def register_scheduled_reminder_trigger(self, task_id: str, reminder_text: str) -> ProactiveContextItem:
        item = ProactiveContextItem(
            id=task_id,
            source="scheduled_reminder",
            summary=f"Reminder: {reminder_text}",
            requires_user_attention=True
        )
        self.proactive_items.append(item)
        self.notifier.notify(
            category=NotificationCategory.REMINDER,
            title="Scheduled Reminder",
            message=reminder_text,
            task_id=task_id
        )
        logger.info(f"ProactiveContextEngine triggered scheduled reminder for task '{task_id}'")
        return item

    def register_task_failure_alert(self, task_id: str, error_msg: str) -> ProactiveContextItem:
        item = ProactiveContextItem(
            id=task_id,
            source="task_failure",
            summary=f"Task '{task_id}' failed: {error_msg}",
            requires_user_attention=True
        )
        self.proactive_items.append(item)
        self.notifier.notify(
            category=NotificationCategory.TASK_FAILED,
            title="Task Execution Failed",
            message=f"Task '{task_id}' encountered error: {error_msg}",
            task_id=task_id
        )
        return item

    def get_active_proactive_context(self) -> List[ProactiveContextItem]:
        return self.proactive_items
