"""
Structured request, result, and audit data models for JARVIS Shell Subsystem.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from jarvis.security.permissions import RiskLevel


class CommandRequest(BaseModel):
    command: str
    arguments: List[str] = Field(default_factory=list)
    working_directory: Optional[str] = None
    environment_overrides: Optional[Dict[str, str]] = None
    timeout: int = 30
    requested_by: str = "agent"
    risk_level: RiskLevel = RiskLevel.LOW


class CommandResult(BaseModel):
    command: str
    arguments: List[str]
    working_directory: str
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: float
    timed_out: bool = False
    cancelled: bool = False
    verified: bool = False
    truncated: bool = False
    risk_level: RiskLevel = RiskLevel.LOW


class AuditRecord(BaseModel):
    operation_id: str
    timestamp: str
    tool_name: str
    executable: str
    full_command: str
    working_directory: str
    risk_level: str
    permission_allowed: bool
    confirmation_required: bool
    confirmed_by_boss: bool
    exit_code: Optional[int] = None
    status: str
    verified: bool
