"""
Orchestration Subsystem Error Hierarchy for JARVIS.
"""


class OrchestrationError(Exception):
    """Base exception for all orchestration errors."""
    pass


class IntentResolutionError(OrchestrationError):
    """Raised when request intent cannot be parsed or resolved."""
    pass


class AmbiguousRequestError(OrchestrationError):
    """Raised when intent or target matches multiple ambiguous candidates."""
    def __init__(self, message: str, candidates: list[str] | None = None):
        super().__init__(message)
        self.candidates = candidates or []


class GoalResolutionError(OrchestrationError):
    """Raised when a goal cannot be formed from an intent."""
    pass


class PlanValidationError(OrchestrationError):
    """Raised when a proposed plan fails validation checks."""
    def __init__(self, message: str, step_id: str | None = None, violations: list[str] | None = None):
        super().__init__(message)
        self.step_id = step_id
        self.violations = violations or []


class ExecutionFailedError(OrchestrationError):
    """Raised when execution of a plan step fails."""
    pass


class ConfirmationRequiredError(OrchestrationError):
    """Raised when high-risk plan step requires explicit user approval."""
    def __init__(self, message: str, confirmation_token: str, action: str, details: dict | None = None):
        super().__init__(message)
        self.confirmation_token = confirmation_token
        self.action = action
        self.details = details or {}


class CancellationRequestedError(OrchestrationError):
    """Raised when execution is interrupted by a user stop/cancel signal."""
    pass


class LoopDetectedError(OrchestrationError):
    """Raised when repeated step/replan loop is detected."""
    pass


class VerificationFailedError(OrchestrationError):
    """Raised when post-condition verification fails."""
    pass
