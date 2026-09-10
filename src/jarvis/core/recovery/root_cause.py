"""
Root Cause Analysis Data Model for JARVIS recovery.
"""

from enum import Enum
from typing import Any, Dict, List
from pydantic import BaseModel, Field
from jarvis.core.recovery.failure import FailureCategory


class ConfidenceLevel(str, Enum):
    """Confidence levels for root cause diagnosis."""
    LIKELY = "LIKELY"
    POSSIBLE = "POSSIBLE"
    UNKNOWN = "UNKNOWN"


class RootCause(BaseModel):
    """Diagnosed root cause explanation with evidence."""

    category: FailureCategory
    confidence: ConfidenceLevel = ConfidenceLevel.UNKNOWN
    evidence: Dict[str, Any] = Field(default_factory=dict)
    likely_causes: List[str] = Field(default_factory=list)
