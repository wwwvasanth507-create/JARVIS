"""
User Takeover & Manual Interference Detector for JARVIS.

Detects when Boss manually interacts with the desktop (active window changed, tab switched)
and cleanly pauses background operations to prevent destructive state overwrites ("Safe Handoff").
"""

import time
import logging
from typing import Dict, Any, Optional

from jarvis.system.event_bus import JarvisEventBus, SystemEventType, SystemEvent
from jarvis.core.tasks.task_manager import LongRunningTaskManager, TaskStatus
from jarvis.system.notification_center import NotificationCenter, NotificationCategory

logger = logging.getLogger(__name__)


class UserTakeoverDetector:
    """Detects manual user interactions and manages background task handoffs."""

    def __init__(self, task_manager: Optional[LongRunningTaskManager] = None, event_bus: Optional[JarvisEventBus] = None, notifier: Optional[NotificationCenter] = None):
        self.task_manager = task_manager or LongRunningTaskManager.get_instance()
        self.event_bus = event_bus or JarvisEventBus.get_instance()
        self.notifier = notifier or NotificationCenter.get_instance()

        # Subscribe to window/application focus events
        self.event_bus.subscribe(SystemEventType.WINDOW_FOCUSED, self._handle_user_window_focus)

    def _handle_user_window_focus(self, event: SystemEvent) -> None:
        """Handles user manual window change by pausing conflicting running tasks."""
        target_app = event.data.get("application") or event.source
        running_tasks = self.task_manager.list_tasks(status=TaskStatus.RUNNING)

        for task in running_tasks:
            active_app_in_task = task.context.get("target_application")
            if active_app_in_task and active_app_in_task.lower() == str(target_app).lower():
                self.task_manager.update_task_status(task.task_id, TaskStatus.PAUSED)
                task.context["pause_reason"] = "User manual interaction detected (Safe Handoff)"
                logger.info(f"UserTakeoverDetector paused task '{task.task_id}' due to user interaction in '{target_app}'.")
                self.notifier.notify(
                    category=NotificationCategory.SYSTEM_WARNING,
                    title="Workflow Paused for User Takeover",
                    message=f"Boss, I paused background task '{task.goal}' because you switched to '{target_app}'.",
                    task_id=task.task_id
                )
