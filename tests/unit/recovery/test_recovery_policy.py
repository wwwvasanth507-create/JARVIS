"""
Unit tests for RecoveryPolicy.
"""

import pytest
from jarvis.core.recovery.errors import HumanInterventionRequiredError, RecoveryPermissionDeniedError
from jarvis.core.recovery.failure import FailureCategory
from jarvis.core.recovery.policy import RecoveryPolicy
from jarvis.core.recovery.root_cause import ConfidenceLevel, RootCause
from jarvis.core.recovery.strategies import RecoveryStrategy, RecoveryStrategyType
from jarvis.security.permissions import RiskLevel


def test_evaluate_high_risk_strategy_denied():
    policy = RecoveryPolicy()
    strat = RecoveryStrategy(
        strategy_id=RecoveryStrategyType.REQUEST_USER,
        description="High risk strategy",
        applicable_failure_types=[FailureCategory.PERMISSION_DENIED],
        risk_level=RiskLevel.HIGH,
    )
    rc = RootCause(category=FailureCategory.PERMISSION_DENIED, confidence=ConfidenceLevel.LIKELY)
    auth, reason = policy.evaluate_recovery_authorization(strat, rc)
    assert auth is False
    assert "high risk" in reason


def test_evaluate_low_confidence_cause_denied():
    policy = RecoveryPolicy()
    strat = RecoveryStrategy(
        strategy_id=RecoveryStrategyType.RETRY_ONCE,
        description="Retry",
        applicable_failure_types=[FailureCategory.TIMEOUT],
        risk_level=RiskLevel.LOW,
    )
    rc = RootCause(category=FailureCategory.UNKNOWN, confidence=ConfidenceLevel.UNKNOWN)
    auth, reason = policy.evaluate_recovery_authorization(strat, rc)
    assert auth is False
    assert "confidence" in reason
