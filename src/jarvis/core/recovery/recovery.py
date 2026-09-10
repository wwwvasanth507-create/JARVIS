"""
Central Recovery Manager for JARVIS recovery subsystem.
Coordinates failure classification, diagnostic evidence gathering, strategy selection,
permission re-checking, recovery execution, diagnostic replanning, and loop protection.
"""

import time
import logging
from typing import Any, Dict, List, Optional, Tuple

from jarvis.core.recovery.classifier import FailureClassifier
from jarvis.core.recovery.diagnostics import DiagnosticEngine
from jarvis.core.recovery.errors import (
    HumanInterventionRequiredError,
    RecoveryError,
    RecoveryLimitExceededError,
    RecoveryLoopDetectedError,
    RecoveryPermissionDeniedError,
)
from jarvis.core.recovery.evidence import DiagnosticEvidence
from jarvis.core.recovery.executor import RecoveryExecutor
from jarvis.core.recovery.failure import FailureCategory, FailureEvent
from jarvis.core.recovery.limits import RecoveryLimits
from jarvis.core.recovery.planner import RecoveryPlan, RecoveryPlanner
from jarvis.core.recovery.policy import RecoveryPolicy
from jarvis.core.recovery.replanner import DiagnosticReplanner
from jarvis.core.recovery.root_cause import ConfidenceLevel, RootCause
from jarvis.core.recovery.state import RecoveryState, RecoveryStatus
from jarvis.core.recovery.strategies import RecoveryStrategy, RecoveryStrategyType, StrategyRegistry
from jarvis.security.permissions import RiskLevel

logger = logging.getLogger("jarvis.core.recovery.recovery")


class JarvisRecoveryManager:
    """
    Main manager for intelligent self-recovery, diagnostics, and replanning.
    Replaces simple retry loops with diagnostic-driven recovery.
    """

    def __init__(
        self,
        limits: Optional[RecoveryLimits] = None,
        classifier: Optional[FailureClassifier] = None,
        diagnostics: Optional[DiagnosticEngine] = None,
        planner: Optional[RecoveryPlanner] = None,
        executor: Optional[RecoveryExecutor] = None,
        policy: Optional[RecoveryPolicy] = None,
        replanner: Optional[DiagnosticReplanner] = None,
    ):
        self.limits = limits or RecoveryLimits()
        self.classifier = classifier or FailureClassifier()
        self.diagnostics = diagnostics or DiagnosticEngine()
        self.planner = planner or RecoveryPlanner()
        self.executor = executor or RecoveryExecutor()
        self.policy = policy or RecoveryPolicy()
        self.replanner = replanner or DiagnosticReplanner()
        self.state_history: Dict[str, RecoveryState] = {}
        self.history_signatures: List[str] = []

    def handle_failure(
        self,
        execution_id: str,
        step_id: str,
        tool_name: str,
        arguments: Dict[str, Any],
        error_message: str,
        verification_result: Optional[Dict[str, Any]] = None,
        retry_count: int = 0,
    ) -> Tuple[bool, Optional[RecoveryPlan], Optional[RootCause]]:
        """
        Coordinates the complete diagnostic recovery lifecycle.
        Returns (can_recover, recovery_plan, root_cause).
        """
        state = self.state_history.get(execution_id)
        if not state:
            state = RecoveryState(execution_id=execution_id)
            self.state_history[execution_id] = state

        state.failure_id = f"fail_{step_id}_{int(time.time())}"
        state.status = RecoveryStatus.DIAGNOSING

        # 1. Construct FailureEvent
        event = FailureEvent(
            execution_id=execution_id,
            step_id=step_id,
            tool_name=tool_name,
            arguments_summary=arguments,
            error_message=error_message,
            verification_result=verification_result or {},
            retry_count=retry_count,
        )

        # 2. Check Loop Detection (3 identical consecutive failures)
        sig = f"{tool_name}:{sorted(arguments.items())}:{error_message}"
        self.history_signatures.append(sig)
        if len(self.history_signatures) >= 3 and self.history_signatures[-3:] == [sig, sig, sig]:
            state.status = RecoveryStatus.FAILED
            raise RecoveryLoopDetectedError(
                f"Repeated identical execution failure loop detected for tool '{tool_name}'."
            )

        # 3. Classify Failure & Run Deterministic Diagnostics
        preliminary_cause = self.classifier.classify(event)
        event.failure_type = preliminary_cause.category

        state.diagnostic_attempts += 1
        if state.diagnostic_attempts > self.limits.max_diagnostic_steps:
            state.status = RecoveryStatus.FAILED
            raise RecoveryLimitExceededError("Exceeded max diagnostic steps budget")

        root_cause, evidence = self.diagnostics.diagnose(event)

        # 4. Strategy Selection
        strategies = StrategyRegistry.get_strategies_for_failure(root_cause.category)
        if not strategies:
            # Default to RETRY_ONCE or REQUEST_USER
            strategies = [StrategyRegistry.get_strategy(RecoveryStrategyType.RETRY_ONCE)]

        selected_strategy = strategies[0]
        state.current_strategy = selected_strategy.strategy_id.value
        state.status = RecoveryStatus.STRATEGY_SELECTED

        # 5. Security & Permission Evaluation
        auth, reason = self.policy.evaluate_recovery_authorization(
            strategy=selected_strategy,
            root_cause=root_cause,
            tool_name=tool_name,
            arguments=arguments,
        )

        if not auth:
            state.status = RecoveryStatus.INTERVENTION_REQUIRED
            raise HumanInterventionRequiredError(
                reason=reason or "Recovery action requires explicit approval",
                blocked_action=tool_name,
                evidence=root_cause.evidence,
                safe_next_action="Confirm recovery action or choose alternative step",
            )

        # 6. Build Recovery Plan
        recovery_plan = self.planner.create_recovery_plan(event, root_cause, selected_strategy)

        state.status = RecoveryStatus.RECOVERING
        return True, recovery_plan, root_cause
