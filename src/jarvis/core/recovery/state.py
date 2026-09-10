"""
Recovery Execution State Tracking for JARVIS recovery.
"""

from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class RecoveryStatus(str, Enum):
    """Detailed recovery state progression statuses."""
    DIAGNOSING = "DIAGNOSING"
    STRATEGY_SELECTED = "STRATEGY_SELECTED"
    WAITING_FOR_PERMISSION = "WAITING_FOR_PERMISSION"
    WAITING_FOR_CONFIRMATION = "WAITING_FOR_CONFIRMATION"
    RECOVERING = "RECOVERING"
    REVERIFYING = "REVERIFYING"
    REPLANNING = "REPLANNING"
    INTERVENTION_REQUIRED = "INTERVENTION_REQUIRED"
    RECOVERED = "RECOVERED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class RecoveryState(BaseModel):
    """State model for tracking active recovery sessions."""

    execution_id: str
    failure_id: Optional[str] = None
    diagnostic_attempts: int = 0
    recovery_attempts: int = 0
    replans: int = 0
    current_strategy: Optional[str] = None
    status: RecoveryStatus = RecoveryStatus.DIAGNOSING
    history_signatures: list[str] = Field(default_factory=list)
    recovery_metrics: Dict[str, Any] = Field(default_factory=dict)
