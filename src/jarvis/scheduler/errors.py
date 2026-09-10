"""
Exception definitions for JARVIS Scheduler Subsystem.
"""

class SchedulerError(Exception):
    """Base exception for all scheduler subsystem errors."""
    pass


class ScheduleParseError(SchedulerError):
    """Raised when natural language schedule expression parsing fails."""
    pass


class TaskNotFoundError(SchedulerError):
    """Raised when requested scheduled task is not found."""
    pass


class TaskStateError(SchedulerError):
    """Raised on invalid state transition requests."""
    pass


class SchedulerPermissionDeniedError(SchedulerError):
    """Raised when runtime permission check fails for a scheduled task execution."""
    pass


class TaskOverlapError(SchedulerError):
    """Raised when task execution overlaps and overlap policy blocks execution."""
    pass
