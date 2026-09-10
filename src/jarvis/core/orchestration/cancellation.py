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

    def is_cancellation_request(self, request_text: str) -> bool:
        normalized = request_text.strip().lower().rstrip(".!")
        return normalized in self.CANCELLATION_KEYWORDS

    def cancel_execution(self, state: ExecutionState, reason: str = "User requested cancellation") -> ExecutionState:
        state.status = ExecutionStatus.CANCELLED
        state.error = reason
        for step in state.pending_steps:
            if hasattr(step, "status"):
                step.status = "CANCELLED"
        return state
