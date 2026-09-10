"""
Recovery Subsystem Exception Definitions for JARVIS.
"""

class RecoveryError(Exception):
    """Base exception for all recovery subsystem errors."""
    pass


class RecoveryLimitExceededError(RecoveryError):
    """Raised when recovery diagnostic, action, or replan limits are exceeded."""
    pass


class RecoveryLoopDetectedError(RecoveryError):
    """Raised when an identical failure recovery loop is detected."""
    pass


class HumanInterventionRequiredError(RecoveryError):
    """Raised when recovery requires explicit human intervention or confirmation."""

    def __init__(self, reason: str, blocked_action: str, evidence: dict, safe_next_action: str):
        super().__init__(reason)
        self.reason = reason
        self.blocked_action = blocked_action
        self.evidence = evidence
        self.safe_next_action = safe_next_action


class DiagnosticFailedError(RecoveryError):
    """Raised when diagnostic engine fails to gather evidence."""
    pass


class RecoveryPermissionDeniedError(RecoveryError):
    """Raised when a recovery action fails permission evaluation."""
    pass
