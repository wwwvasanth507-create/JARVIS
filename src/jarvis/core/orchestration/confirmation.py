"""
Confirmation Manager for JARVIS orchestration.
"""

import time
import uuid
from typing import Dict, Optional, Any
from pydantic import BaseModel, Field


class PendingConfirmation(BaseModel):
    token: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    action: str
    arguments: Dict[str, Any]
    description: str
    risk_level: str
    created_at: float = Field(default_factory=time.time)
    expires_in_seconds: float = 300.0  # 5 minutes


class ConfirmationManager:
    """Manages high-risk action confirmation tokens and validation."""

    def __init__(self):
        self._pending: Dict[str, PendingConfirmation] = {}

    def request_confirmation(
        self,
        action: str,
        arguments: Dict[str, Any],
        description: str,
        risk_level: str,
    ) -> PendingConfirmation:
        pending = PendingConfirmation(
            action=action,
            arguments=arguments,
            description=description,
            risk_level=risk_level,
        )
        self._pending[pending.token] = pending
        return pending

    def validate_confirmation(self, token: Optional[str]) -> tuple[bool, Optional[PendingConfirmation], str]:
        if not token:
            return False, None, "No confirmation token provided."

        pending = self._pending.get(token)
        if not pending:
            return False, None, "Invalid confirmation token."

        now = time.time()
        if now - pending.created_at > pending.expires_in_seconds:
            del self._pending[token]
            return False, None, "Confirmation token expired."

        # Valid token — consume it
        del self._pending[token]
        return True, pending, "Confirmation token validated successfully."

    def clear(self) -> None:
        self._pending.clear()
