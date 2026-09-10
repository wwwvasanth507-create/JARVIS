"""
Recovery Planner for JARVIS recovery.
Constructs RecoveryPlan steps based on FailureEvent, RootCause, and selected RecoveryStrategy.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from jarvis.core.recovery.failure import FailureCategory, FailureEvent
from jarvis.core.recovery.root_cause import RootCause
from jarvis.core.recovery.strategies import RecoveryStrategy, RecoveryStrategyType
from jarvis.security.permissions import RiskLevel


class RecoveryStep(BaseModel):
    """Individual step in a recovery plan."""

    step_id: str
    tool_name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    risk_level: RiskLevel = RiskLevel.LOW
    description: str = ""
    expected_outcome: str = ""


class RecoveryPlan(BaseModel):
    """Structured plan containing recovery steps."""

    plan_id: str
    strategy: RecoveryStrategyType
    steps: List[RecoveryStep] = Field(default_factory=list)
    risk_level: RiskLevel = RiskLevel.LOW
    description: str = ""


class RecoveryPlanner:
    """Constructs targeted recovery plans."""

    def create_recovery_plan(
        self,
        event: FailureEvent,
        root_cause: RootCause,
        strategy: RecoveryStrategy
    ) -> RecoveryPlan:
        """Generates RecoveryPlan steps from failure diagnosis."""
        steps: List[RecoveryStep] = []

        if strategy.strategy_id == RecoveryStrategyType.RETRY_ONCE:
            steps.append(
                RecoveryStep(
                    step_id="step_recovery_retry",
                    tool_name=event.tool_name,
                    arguments=event.arguments_summary,
                    risk_level=strategy.risk_level,
                    description=f"Retry {event.tool_name} once",
                    expected_outcome=strategy.expected_outcome,
                )
            )

        elif strategy.strategy_id == RecoveryStrategyType.REFRESH_STATE:
            steps.append(
                RecoveryStep(
                    step_id="step_recovery_capture",
                    tool_name="screen.capture",
                    arguments={"mode": "ACTIVE_WINDOW"},
                    risk_level=RiskLevel.LOW,
                    description="Capture fresh screen state",
                    expected_outcome="Updated visual state obtained",
                )
            )

        elif strategy.strategy_id == RecoveryStrategyType.REFRESH_APPLICATION_REGISTRY:
            steps.append(
                RecoveryStep(
                    step_id="step_recovery_apps",
                    tool_name="application.list",
                    arguments={},
                    risk_level=RiskLevel.LOW,
                    description="Refresh installed application registry",
                    expected_outcome="Application path index refreshed",
                )
            )

        elif strategy.strategy_id == RecoveryStrategyType.RELOAD_BROWSER_PAGE:
            steps.append(
                RecoveryStep(
                    step_id="step_recovery_browser_reload",
                    tool_name="browser.navigate",
                    arguments={"url": event.arguments_summary.get("url", "about:blank")},
                    risk_level=RiskLevel.LOW,
                    description="Reload current browser page",
                    expected_outcome="Page reloaded",
                )
            )

        elif strategy.strategy_id == RecoveryStrategyType.REQUERY_FILESYSTEM:
            target_name = event.arguments_summary.get("path", "")
            if isinstance(target_name, str):
                target_name = target_name.replace("\\", "/").split("/")[-1]
            steps.append(
                RecoveryStep(
                    step_id="step_recovery_fs_search",
                    tool_name="filesystem.find",
                    arguments={"name": target_name or "*"},
                    risk_level=RiskLevel.LOW,
                    description=f"Search permitted directories for '{target_name}'",
                    expected_outcome="Alternative file candidates located",
                )
            )

        return RecoveryPlan(
            plan_id=f"rec_{event.failure_id[:8]}",
            strategy=strategy.strategy_id,
            steps=steps,
            risk_level=strategy.risk_level,
            description=f"Recovery plan using {strategy.strategy_id.value}",
        )
