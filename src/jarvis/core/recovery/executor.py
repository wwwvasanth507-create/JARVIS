"""
Recovery Executor for JARVIS recovery.
Executes recovery steps with mandatory permission re-checks and verification.
"""

import time
import logging
from typing import Dict, Any, Tuple
from jarvis.core.orchestration.dispatcher import ToolDispatcher
from jarvis.core.recovery.policy import RecoveryPolicy
from jarvis.core.recovery.planner import RecoveryPlan, RecoveryStep
from jarvis.core.recovery.root_cause import RootCause
from jarvis.core.recovery.strategies import RecoveryStrategy, StrategyRegistry, RecoveryStrategyType

logger = logging.getLogger("jarvis.core.recovery.executor")


class RecoveryExecutor:
    """Executes recovery plan steps with security re-checks."""

    def __init__(self, dispatcher: Optional[ToolDispatcher] = None, policy: Optional[RecoveryPolicy] = None):
        self.dispatcher = dispatcher or ToolDispatcher()
        self.policy = policy or RecoveryPolicy()

    def execute_recovery_plan(
        self,
        plan: RecoveryPlan,
        root_cause: RootCause
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Executes each step in RecoveryPlan.
        """
        strategy = StrategyRegistry.get_strategy(plan.strategy) or RecoveryStrategy(
            strategy_id=plan.strategy,
            description="Custom recovery strategy",
            applicable_failure_types=[root_cause.category],
            risk_level=plan.risk_level,
        )

        for step in plan.steps:
            # Mandatory permission re-check
            auth, reason = self.policy.evaluate_recovery_authorization(
                strategy=strategy,
                root_cause=root_cause,
                tool_name=step.tool_name,
                arguments=step.arguments,
            )
            if not auth:
                return False, f"Recovery step '{step.step_id}' unauthorized: {reason}", {}

            # Dispatch recovery action
            t0 = time.time()
            res = self.dispatcher.dispatch(step.tool_name, step.arguments)
            dur = time.time() - t0

            if not res.success:
                return False, f"Recovery tool '{step.tool_name}' failed: {res.message}", {}

        return True, "Recovery steps executed successfully", {"duration_seconds": dur}
