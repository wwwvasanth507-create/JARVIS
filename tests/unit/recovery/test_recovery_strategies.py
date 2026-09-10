"""
Unit tests for StrategyRegistry.
"""

from jarvis.core.recovery.failure import FailureCategory
from jarvis.core.recovery.strategies import StrategyRegistry, RecoveryStrategyType


def test_get_strategy_by_id():
    strat = StrategyRegistry.get_strategy(RecoveryStrategyType.RETRY_ONCE)
    assert strat is not None
    assert strat.strategy_id == RecoveryStrategyType.RETRY_ONCE


def test_get_strategies_for_failure():
    strats = StrategyRegistry.get_strategies_for_failure(FailureCategory.TIMEOUT)
    assert len(strats) > 0
    strat_ids = [s.strategy_id for s in strats]
    assert RecoveryStrategyType.RETRY_ONCE in strat_ids
