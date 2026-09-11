"""
Target Lease for UI Element Action Security & Freshness.
"""

import time
import hashlib
import json
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from jarvis.computer.vision.ui_element import UIElement


class TargetLease(BaseModel):
    """
    Temporary Target Lease valid for action execution.
    Validates freshness and screen state hash before performing side-effect actions.
    """
    lease_id: str
    element: UIElement
    source: str
    confidence: float
    created_at: float = Field(default_factory=time.time)
    expires_at: float
    state_hash: str

    def is_valid(self, current_state_hash: Optional[str] = None, max_age_sec: float = 15.0) -> bool:
        now = time.time()
        if now > self.expires_at or (now - self.created_at) > max_age_sec:
            return False
        if current_state_hash and self.state_hash != current_state_hash:
            return False
        return True

    @classmethod
    def create(cls, element: UIElement, state_hash: str, ttl_sec: float = 15.0) -> "TargetLease":
        now = time.time()
        lease_id = hashlib.sha256(f"{element.id}:{now}:{state_hash}".encode()).hexdigest()[:16]
        return cls(
            lease_id=lease_id,
            element=element,
            source=element.source.value,
            confidence=element.get_effective_confidence(),
            created_at=now,
            expires_at=now + ttl_sec,
            state_hash=state_hash,
        )
