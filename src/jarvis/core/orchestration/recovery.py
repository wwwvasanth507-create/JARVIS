"""
Recovery and Loop Detection Manager for JARVIS orchestration.
"""

from typing import Any, Dict, List, Optional
from jarvis.core.orchestration.errors import LoopDetectedError
from jarvis.core.orchestration.plan import Plan, PlanStep, PlanStepStatus
from jarvis.security.permissions import RiskLevel


class RecoveryManager:
    """Handles step retries, replanning, and loop prevention."""

    def __init__(self, max_retries_per_step: int = 1, max_replans: int = 2):
        self.max_retries_per_step = max_retries_per_step
        self.max_replans = max_replans
        self.replan_count = 0
        self.history_signatures: List[str] = []

    def can_retry_step(self, step: PlanStep) -> bool:
        # High risk actions never auto-retry
        if step.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL):
            return False
        
        current_retries = step.retry_policy.get("retry_count", 0)
        return current_retries < self.max_retries_per_step

    def record_step_retry(self, step: PlanStep) -> None:
        count = step.retry_policy.get("retry_count", 0)
        step.retry_policy["retry_count"] = count + 1

    def track_action(self, tool_name: str, arguments: Dict[str, Any], error: Optional[str]) -> None:
        sig = f"{tool_name}:{sorted(arguments.items())}:{error}"
        self.history_signatures.append(sig)
        
        # Check if the exact same tool failure occurred 3 times in a row
        if len(self.history_signatures) >= 3:
            recent = self.history_signatures[-3:]
            if recent[0] == recent[1] == recent[2]:
                raise LoopDetectedError(
                    f"Repeated identical execution failure loop detected for tool '{tool_name}'."
                )

    def can_replan(self) -> bool:
        return self.replan_count < self.max_replans

    def record_replan(self) -> None:
        self.replan_count += 1
