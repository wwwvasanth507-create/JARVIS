"""
Custom exceptions for the JARVIS Application Control Subsystem.
"""


class ApplicationError(Exception):
    """Base exception for all application management operations in JARVIS."""
    pass


class ApplicationNotFound(ApplicationError):
    """Raised when a requested application cannot be resolved by name or alias."""
    pass


class ApplicationLaunchFailed(ApplicationError):
    """Raised when an application fails to start or pass launch verification."""
    pass


class ApplicationCloseFailed(ApplicationError):
    """Raised when an application fails to close gracefully."""
    pass


class AmbiguousApplication(ApplicationError):
    """Raised when a natural language application query matches multiple distinct candidates."""
    def __init__(self, query: str, candidates: list[str]):
        self.query = query
        self.candidates = candidates
        cand_str = ", ".join(candidates)
        super().__init__(
            f"Ambiguous application query '{query}' matched multiple candidates: [{cand_str}]. "
            "Please clarify which application you meant, Boss."
        )


class ApplicationPermissionDenied(ApplicationError):
    """Raised when an application action violates security policy."""
    pass


class ApplicationNotRunning(ApplicationError):
    """Raised when an operation requires an application to be running, but it is not."""
    pass


class ApplicationHealthError(ApplicationError):
    """Raised when an application health check fails."""
    pass


class ProtectedApplicationBlocked(ApplicationError):
    """Raised when an operation attempts to modify or terminate a protected system app."""
    pass


class UnsavedWorkWarning(ApplicationError):
    """Raised or returned when closing an application that has unsaved work."""
    pass
