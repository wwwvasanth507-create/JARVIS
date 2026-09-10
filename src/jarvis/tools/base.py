"""
Generic Tool Abstraction Interface for JARVIS.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from jarvis.security.permissions import PermissionCategory, RiskLevel


class ToolMetadata(BaseModel):
    name: str = Field(..., description="Qualified tool identifier e.g. browser.search")
    description: str = Field(..., description="Human-readable description of what the tool does")
    input_schema: Dict[str, Any] = Field(default_factory=dict, description="JSON schema / parameters spec")
    permission_requirement: PermissionCategory = Field(..., description="Required security category")
    risk_level: RiskLevel = Field(..., description="Inherent risk level tier")
    verification_strategy: str = Field(default="state_check", description="Strategy used to verify state change")


class ToolResultStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    DENIED = "DENIED"
    CONFIRMATION_REQUIRED = "CONFIRMATION_REQUIRED"
    AMBIGUOUS = "AMBIGUOUS"
    NOT_FOUND = "NOT_FOUND"
    TIMEOUT = "TIMEOUT"
    CANCELLED = "CANCELLED"
    VERIFICATION_FAILED = "VERIFICATION_FAILED"


class ToolResult(BaseModel):
    success: bool
    status: ToolResultStatus = ToolResultStatus.SUCCESS
    data: Optional[Any] = None
    error: Optional[str] = None
    observations: Optional[Dict[str, Any]] = None
    verification: Optional[Dict[str, Any]] = None
    verification_details: Optional[Dict[str, Any]] = None
    duration_ms: float = 0.0


class BaseTool(ABC):
    """Abstract Base Class for all JARVIS Tools."""

    def __init__(self, metadata: ToolMetadata):
        self.metadata = metadata

    @property
    def name(self) -> str:
        return self.metadata.name

    @abstractmethod
    def execute(self, **kwargs: Any) -> ToolResult:
        """Executes the tool action."""
        pass

    @abstractmethod
    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        """Verifies if the action actually succeeded in changing state."""
        pass

    def handle_error(self, exception: Exception) -> ToolResult:
        """Standard error handler for tool exceptions."""
        return ToolResult(
            success=False,
            error=f"Tool Execution Error [{self.name}]: {str(exception)}",
        )
