"""
Cancellation Manager for JARVIS orchestration.
"""

from typing import Optional
from jarvis.core.orchestration.state import ExecutionState, ExecutionStatus


class CancellationManager:
    """Detects cancellation signals and updates execution state."""

    CANCELLATION_KEYWORDS = {
        "stop",
        "cancel",
        "never mind",
        "nevermind",
        "abort",
        "halt",
        "cancel that",
        "stop execution",
    }

    def __init__(self):
        self._cancellation_requested = False
        self._cancellation_reason = ""

    def request_cancellation(self, reason: str = "User requested cancellation") -> None:
        """Sets the global cancellation request flag and reason."""
        self._cancellation_requested = True
        self._cancellation_reason = reason

    def is_cancellation_requested(self) -> bool:
        """Checks if a cancellation request is pending."""
        return self._cancellation_requested

    def reset_cancellation(self) -> None:
        """Resets the cancellation flag."""
        self._cancellation_requested = False
        self._cancellation_reason = ""

    def is_cancellation_request(self, request_text: str) -> bool:
        normalized = request_text.strip().lower().rstrip(".!")
        return normalized in self.CANCELLATION_KEYWORDS or self._cancellation_requested

    def cancel_execution(self, state: ExecutionState, reason: str = "User requested cancellation") -> ExecutionState:
        state.status = ExecutionStatus.CANCELLED
        state.error = reason or self._cancellation_reason
        for step in state.pending_steps:
            if hasattr(step, "status"):
                step.status = "CANCELLED"
        self.reset_cancellation()
        return state
