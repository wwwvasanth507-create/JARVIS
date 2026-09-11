"""
Unit tests for GoalPolicy, autonomy levels 0-3, and security constraints.
"""

import pytest
from jarvis.core.goals.models import Goal, Objective, AutonomyLevel
from jarvis.core.goals.policy import GoalPolicy, GoalPolicyError
from jarvis.security.permissions import RiskLevel


def test_autonomy_level_high_risk_confirmation():
    policy = GoalPolicy()
    g_level3 = Goal(title="Scheduled Goal", autonomy_level=AutonomyLevel.LEVEL_3_SCHEDULED)

    # Low risk -> Allowed under Level 3
    assert policy.validate_autonomy_level(g_level3, RiskLevel.LOW) is True

    # High/Critical risk -> Requires confirmation even under Level 3
    assert policy.validate_autonomy_level(g_level3, RiskLevel.HIGH) is False
    assert policy.validate_autonomy_level(g_level3, RiskLevel.CRITICAL) is False


def test_autonomy_level_manual_mode():
    policy = GoalPolicy()
    g_manual = Goal(title="Manual Goal", autonomy_level=AutonomyLevel.LEVEL_0_MANUAL)

    # Level 0 manual mode requires confirmation for all actions
    assert policy.validate_autonomy_level(g_manual, RiskLevel.LOW) is False


def test_max_active_goals_limit():
    policy = GoalPolicy(max_active_goals=2)
    g = Goal(title="Sample Goal")

    policy.validate_goal_creation(g, current_active_count=1)
    with pytest.raises(GoalPolicyError):
        policy.validate_goal_creation(g, current_active_count=2)


def test_cycle_detection():
    policy = GoalPolicy()
    obj1 = Objective(goal_id="g1", title="Obj 1")
    obj2 = Objective(goal_id="g1", title="Obj 2", dependencies=[obj1.objective_id])
    obj1.dependencies.append(obj2.objective_id)  # Create cycle

    with pytest.raises(GoalPolicyError):
        policy.detect_objective_cycles([obj1, obj2])
