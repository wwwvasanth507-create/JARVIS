"""
Strategy Memory & Historical Failure Pattern Memory for JARVIS.

Records verified successful workflow strategies and historical failure recovery patterns
without overriding current observations or security policy.
"""

import time
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class StrategyRecord(BaseModel):
    strategy_id: str
    goal_pattern: str
    successful_tools: List[str]
    context_hints: Dict[str, Any] = Field(default_factory=dict)
    use_count: int = 1
    last_used: float = Field(default_factory=time.time)


class FailurePatternRecord(BaseModel):
    pattern_id: str
    tool_name: str
    error_signature: str
    effective_recovery_action: str
    occurrence_count: int = 1
    last_occurred: float = Field(default_factory=time.time)


class StrategyMemory:
    """Manages successful strategy records and failure patterns."""

    _instance: Optional["StrategyMemory"] = None

    def __init__(self):
        self._strategies: Dict[str, StrategyRecord] = {}
        self._failures: Dict[str, FailurePatternRecord] = {}

    @classmethod
    def get_instance(cls) -> "StrategyMemory":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def record_successful_strategy(self, goal_pattern: str, successful_tools: List[str], context_hints: Optional[Dict[str, Any]] = None) -> StrategyRecord:
        key = goal_pattern.lower().strip()
        if key in self._strategies:
            rec = self._strategies[key]
            rec.use_count += 1
            rec.last_used = time.time()
            return rec

        rec = StrategyRecord(
            strategy_id=f"strat_{len(self._strategies)+1}",
            goal_pattern=goal_pattern,
            successful_tools=successful_tools,
            context_hints=context_hints or {}
        )
        self._strategies[key] = rec
        logger.info(f"StrategyMemory recorded successful strategy for '{goal_pattern}' using {successful_tools}")
        return rec

    def find_strategy_guidance(self, goal: str) -> Optional[StrategyRecord]:
        goal_lower = goal.lower()
        for key, rec in self._strategies.items():
            if key in goal_lower or goal_lower in key:
                return rec
        return None

    def record_failure_pattern(self, tool_name: str, error_sig: str, recovery_action: str) -> FailurePatternRecord:
        key = f"{tool_name}:{error_sig}"
        if key in self._failures:
            rec = self._failures[key]
            rec.occurrence_count += 1
            rec.last_occurred = time.time()
            return rec

        rec = FailurePatternRecord(
            pattern_id=f"fail_{len(self._failures)+1}",
            tool_name=tool_name,
            error_signature=error_sig,
            effective_recovery_action=recovery_action
        )
        self._failures[key] = rec
        logger.info(f"StrategyMemory recorded failure pattern '{key}' -> {recovery_action}")
        return rec

    def get_recovery_recommendation(self, tool_name: str, error_sig: str) -> Optional[str]:
        key = f"{tool_name}:{error_sig}"
        rec = self._failures.get(key)
        return rec.effective_recovery_action if rec else None
