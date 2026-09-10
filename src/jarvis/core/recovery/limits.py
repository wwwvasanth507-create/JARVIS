"""
Recovery Limits and Budget Configuration for JARVIS recovery.
"""

from pydantic import BaseModel, Field


class RecoveryLimits(BaseModel):
    """Configurable execution budget limits to keep recovery fast and bounded."""

    max_diagnostic_steps: int = Field(default=3, description="Max diagnostic gathering steps allowed")
    max_recovery_steps: int = Field(default=3, description="Max recovery action steps allowed per failure")
    max_replans: int = Field(default=2, description="Max plan rebuild attempts allowed")
    max_total_recovery_time: int = Field(default=60, description="Max total seconds spent in recovery")
