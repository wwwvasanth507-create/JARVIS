"""
JARVIS Scheduler and Background Automation Subsystem.
"""

from jarvis.scheduler.errors import (
    SchedulerError,
    ScheduleParseError,
    TaskNotFoundError,
    TaskStateError,
    SchedulerPermissionDeniedError,
    TaskOverlapError,
)
from jarvis.scheduler.models import TaskPriority, TaskState, ScheduledTask, TaskRun
from jarvis.scheduler.recurrence import RecurrenceType, RecurrencePattern
from jarvis.scheduler.parser import ScheduleParser
from jarvis.scheduler.persistence import TaskPersistence
from jarvis.scheduler.notifications import NotificationManager
from jarvis.scheduler.policy import SchedulerPolicy
from jarvis.scheduler.queue import BoundedSchedulerQueue
from jarvis.scheduler.worker import TaskWorkerPool
from jarvis.scheduler.executor import TaskExecutor
from jarvis.scheduler.cancellation import TaskCanceller
from jarvis.scheduler.recovery import SchedulerRecovery
from jarvis.scheduler.verification import TaskVerification
from jarvis.scheduler.scheduler import TaskScheduler
from jarvis.scheduler.manager import SchedulerManager

__all__ = [
    "SchedulerError",
    "ScheduleParseError",
    "TaskNotFoundError",
    "TaskStateError",
    "SchedulerPermissionDeniedError",
    "TaskOverlapError",
    "TaskPriority",
    "TaskState",
    "ScheduledTask",
    "TaskRun",
    "RecurrenceType",
    "RecurrencePattern",
    "ScheduleParser",
    "TaskPersistence",
    "NotificationManager",
    "SchedulerPolicy",
    "BoundedSchedulerQueue",
    "TaskWorkerPool",
    "TaskExecutor",
    "TaskCanceller",
    "SchedulerRecovery",
    "TaskVerification",
    "TaskScheduler",
    "SchedulerManager",
]
