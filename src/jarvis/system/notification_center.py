"""
Internal Event Notification Center for JARVIS.

Manages desktop alerts, system warnings, task status updates, and history
across 7 categories (TASK_COMPLETE, TASK_FAILED, TASK_REQUIRES_INPUT,
TASK_REQUIRES_CONFIRMATION, SYSTEM_WARNING, SYSTEM_ERROR, REMINDER).
"""

from enum import Enum
import uuid
import time
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class NotificationCategory(str, Enum):
    TASK_COMPLETE = "TASK_COMPLETE"
    TASK_FAILED = "TASK_FAILED"
    TASK_REQUIRES_INPUT = "TASK_REQUIRES_INPUT"
    TASK_REQUIRES_CONFIRMATION = "TASK_REQUIRES_CONFIRMATION"
    SYSTEM_WARNING = "SYSTEM_WARNING"
    SYSTEM_ERROR = "SYSTEM_ERROR"
    REMINDER = "REMINDER"


class NotificationItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    category: NotificationCategory
    title: str
    message: str
    task_id: Optional[str] = None
    read: bool = False
    timestamp: float = Field(default_factory=time.time)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class NotificationCenter:
    """Singleton Notification Center managing system alerts and notification history."""

    _instance: Optional["NotificationCenter"] = None

    def __init__(self):
        self._notifications: List[NotificationItem] = []
        self._max_history: int = 100

    @classmethod
    def get_instance(cls) -> "NotificationCenter":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def notify(self, category: NotificationCategory, title: str, message: str, task_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> NotificationItem:
        item = NotificationItem(
            category=category,
            title=title,
            message=message,
            task_id=task_id,
            metadata=metadata or {}
        )
        self._notifications.append(item)
        if len(self._notifications) > self._max_history:
            self._notifications.pop(0)

        logger.info(f"NotificationCenter [{category.value}] {title}: {message}")
        return item

    def get_notifications(self, unread_only: bool = False, category: Optional[NotificationCategory] = None) -> List[NotificationItem]:
        res = self._notifications
        if unread_only:
            res = [n for n in res if not n.read]
        if category:
            res = [n for n in res if n.category == category]
        return list(reversed(res))

    def mark_read(self, notification_id: str) -> bool:
        for n in self._notifications:
            if n.id == notification_id:
                n.read = True
                return True
        return False

    def clear_all(self) -> None:
        self._notifications.clear()
