"""
Recovery Security Policy and Permission Evaluator Integration for JARVIS recovery.
"""

import logging
from typing import Tuple, Dict, Any, Optional
from jarvis.core.recovery.errors import RecoveryPermissionDeniedError, HumanInterventionRequiredError
from jarvis.core.recovery.failure import FailureCategory
from jarvis.core.recovery.root_cause import ConfidenceLevel, RootCause
from jarvis.core.recovery.strategies import RecoveryStrategy, RecoveryStrategyType
from jarvis.security.permissions import PermissionEvaluator, RiskLevel, PermissionCategory

logger = logging.getLogger("jarvis.core.recovery.policy")


class RecoveryPolicy:
    """
    Enforces security boundaries, risk escalation rules, permission re-checking,
    and automatic vs. human-intervention recovery decisions.
    """

    def __init__(self, permission_evaluator: Optional[PermissionEvaluator] = None):
        self.permission_evaluator = permission_evaluator or PermissionEvaluator()

    def evaluate_recovery_authorization(
        self,
        strategy: RecoveryStrategy,
        root_cause: RootCause,
        tool_name: Optional[str] = None,
        arguments: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Determines whether recovery action is authorized automatically or requires human intervention.
        """
        # 1. Require human intervention for HIGH / CRITICAL risk strategies
        if strategy.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL):
            return False, f"Recovery strategy '{strategy.strategy_id}' has high risk ({strategy.risk_level.value})"

        # 2. Require human intervention if confidence is LOW or UNKNOWN
        if root_cause.confidence not in (ConfidenceLevel.LIKELY, ConfidenceLevel.POSSIBLE):
            return False, f"Root cause confidence is '{root_cause.confidence.value}', requiring human intervention"

        # 3. Require human intervention if category is PERMISSION_DENIED or AMBIGUOUS
        if root_cause.category in (FailureCategory.PERMISSION_DENIED, FailureCategory.AMBIGUOUS):
            return False, f"Failure category '{root_cause.category.value}' requires human intervention"

        # 4. Mandatory Permission Re-Check on recovery tool
        if tool_name:
            args = arguments or {}
            # Map tool category
            cat = PermissionCategory.COMPUTER_CONTROL
            if "screen" in tool_name or "vision" in tool_name:
                cat = PermissionCategory.SCREEN_READ
            elif "filesystem" in tool_name or "file" in tool_name:
                cat = PermissionCategory.READ_FILES if ("read" in tool_name or "find" in tool_name) else PermissionCategory.WRITE_FILES
            elif "browser" in tool_name:
                cat = PermissionCategory.BROWSER_CONTROL
            elif "application" in tool_name or "app" in tool_name:
                cat = PermissionCategory.APPLICATION_CONTROL
            elif "shell" in tool_name:
                cat = PermissionCategory.RUN_COMMANDS

            decision = self.permission_evaluator.evaluate(cat, strategy.risk_level, tool_name, args)
            if not decision.allowed:
                raise RecoveryPermissionDeniedError(
                    f"Recovery action tool '{tool_name}' failed permission check: {decision.reason}"
                )

        return True, None
