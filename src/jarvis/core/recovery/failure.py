"""
Failure Taxonomy and Event Data Model for JARVIS recovery.
"""

import time
import uuid
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class FailureCategory(str, Enum):
    """Extensible categories of execution failures."""
    NOT_FOUND = "NOT_FOUND"
    AMBIGUOUS = "AMBIGUOUS"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    TIMEOUT = "TIMEOUT"
    NETWORK_ERROR = "NETWORK_ERROR"
    APPLICATION_NOT_READY = "APPLICATION_NOT_READY"
    VISUAL_TARGET_NOT_FOUND = "VISUAL_TARGET_NOT_FOUND"
    VERIFICATION_FAILED = "VERIFICATION_FAILED"
    INVALID_ARGUMENT = "INVALID_ARGUMENT"
    RESOURCE_UNAVAILABLE = "RESOURCE_UNAVAILABLE"
    PATH_INVALID = "PATH_INVALID"
    PROCESS_FAILED = "PROCESS_FAILED"
    MODEL_ERROR = "MODEL_ERROR"
    DEPENDENCY_MISSING = "DEPENDENCY_MISSING"
    STATE_CHANGED = "STATE_CHANGED"
    UNKNOWN = "UNKNOWN"


class FailureEvent(BaseModel):
    """Structured event capturing failure details without storing sensitive payload content."""

    failure_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    execution_id: str
    step_id: str
    tool_name: str
    arguments_summary: Dict[str, Any] = Field(default_factory=dict)
    failure_type: FailureCategory = FailureCategory.UNKNOWN
    error_code: Optional[str] = None
    error_message: str = ""
    observations: List[Dict[str, Any]] = Field(default_factory=list)
    verification_result: Dict[str, Any] = Field(default_factory=dict)
    timestamp: float = Field(default_factory=time.time)
    retry_count: int = 0
