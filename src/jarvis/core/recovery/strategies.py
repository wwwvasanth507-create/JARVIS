"""
Recovery Strategies and Registry for JARVIS recovery.
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from jarvis.core.recovery.failure import FailureCategory
from jarvis.security.permissions import RiskLevel


class RecoveryStrategyType(str, Enum):
    """Supported recovery strategy types."""
    RETRY_ONCE = "RETRY_ONCE"
    REFRESH_STATE = "REFRESH_STATE"
    REDISCOVER_TARGET = "REDISCOVER_TARGET"
    REFRESH_APPLICATION_REGISTRY = "REFRESH_APPLICATION_REGISTRY"
    REOPEN_APPLICATION = "REOPEN_APPLICATION"
    RELOAD_BROWSER_PAGE = "RELOAD_BROWSER_PAGE"
    REQUERY_FILESYSTEM = "REQUERY_FILESYSTEM"
    REBUILD_PLAN = "REBUILD_PLAN"
    REQUEST_USER = "REQUEST_USER"


class RecoveryStrategy(BaseModel):
    """Structured recovery strategy definition."""

    strategy_id: RecoveryStrategyType
    description: str
    applicable_failure_types: List[FailureCategory]
    required_tools: List[str] = Field(default_factory=list)
    risk_level: RiskLevel = RiskLevel.LOW
    expected_outcome: str = ""


class StrategyRegistry:
    """Registry mapping failure categories to appropriate recovery strategies."""

    _STRATEGIES: Dict[RecoveryStrategyType, RecoveryStrategy] = {
        RecoveryStrategyType.RETRY_ONCE: RecoveryStrategy(
            strategy_id=RecoveryStrategyType.RETRY_ONCE,
            description="Re-attempt the failed action once without modifying parameters",
            applicable_failure_types=[FailureCategory.TIMEOUT, FailureCategory.NETWORK_ERROR],
            risk_level=RiskLevel.LOW,
            expected_outcome="Transient network or process delay resolves",
        ),
        RecoveryStrategyType.REFRESH_STATE: RecoveryStrategy(
            strategy_id=RecoveryStrategyType.REFRESH_STATE,
            description="Capture fresh screen and window state before continuing",
            applicable_failure_types=[FailureCategory.STATE_CHANGED, FailureCategory.VISUAL_TARGET_NOT_FOUND],
            required_tools=["screen.capture"],
            risk_level=RiskLevel.LOW,
            expected_outcome="Visual screen state refreshed",
        ),
        RecoveryStrategyType.REFRESH_APPLICATION_REGISTRY: RecoveryStrategy(
            strategy_id=RecoveryStrategyType.REFRESH_APPLICATION_REGISTRY,
            description="Rescan installed desktop applications to discover updated launch path",
            applicable_failure_types=[FailureCategory.APPLICATION_NOT_READY, FailureCategory.NOT_FOUND],
            required_tools=["application.list"],
            risk_level=RiskLevel.LOW,
            expected_outcome="Application path cache refreshed",
        ),
        RecoveryStrategyType.RELOAD_BROWSER_PAGE: RecoveryStrategy(
            strategy_id=RecoveryStrategyType.RELOAD_BROWSER_PAGE,
            description="Reload current browser page and wait for DOM readiness",
            applicable_failure_types=[FailureCategory.TIMEOUT, FailureCategory.VERIFICATION_FAILED],
            required_tools=["browser.navigate"],
            risk_level=RiskLevel.LOW,
            expected_outcome="Page DOM reloaded",
        ),
        RecoveryStrategyType.REQUERY_FILESYSTEM: RecoveryStrategy(
            strategy_id=RecoveryStrategyType.REQUERY_FILESYSTEM,
            description="Search alternative permitted folders for missing target file",
            applicable_failure_types=[FailureCategory.PATH_INVALID, FailureCategory.NOT_FOUND],
            required_tools=["filesystem.find"],
            risk_level=RiskLevel.LOW,
            expected_outcome="Alternative file candidate located",
        ),
        RecoveryStrategyType.REBUILD_PLAN: RecoveryStrategy(
            strategy_id=RecoveryStrategyType.REBUILD_PLAN,
            description="Rebuild plan based on diagnostic findings",
            applicable_failure_types=[FailureCategory.VERIFICATION_FAILED, FailureCategory.STATE_CHANGED],
            risk_level=RiskLevel.MEDIUM,
            expected_outcome="New validated plan constructed",
        ),
        RecoveryStrategyType.REQUEST_USER: RecoveryStrategy(
            strategy_id=RecoveryStrategyType.REQUEST_USER,
            description="Request human intervention / confirmation from Boss",
            applicable_failure_types=[FailureCategory.PERMISSION_DENIED, FailureCategory.AMBIGUOUS],
            risk_level=RiskLevel.HIGH,
            expected_outcome="Human guidance received",
        ),
    }

    @classmethod
    def get_strategy(cls, strategy_id: RecoveryStrategyType) -> Optional[RecoveryStrategy]:
        return cls._STRATEGIES.get(strategy_id)

    @classmethod
    def get_strategies_for_failure(cls, category: FailureCategory) -> List[RecoveryStrategy]:
        return [s for s in cls._STRATEGIES.values() if category in s.applicable_failure_types]
