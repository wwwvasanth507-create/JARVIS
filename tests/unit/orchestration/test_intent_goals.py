"""
Unit tests for Intent understanding and Goal resolution.
"""

from jarvis.core.orchestration.goals import GoalResolver
from jarvis.core.orchestration.intent import IntentConfidence, IntentParser
from jarvis.security.permissions import RiskLevel


def test_fast_path_intent_parsing():
    parser = IntentParser()

    # Open app
    intent = parser.parse("Open Chrome")
    assert intent.is_fast_path is True
    assert intent.action == "application.open"
    assert intent.target == "Chrome"
    assert intent.confidence == IntentConfidence.HIGH

    # Close app
    intent_close = parser.parse("Close Calculator")
    assert intent_close.is_fast_path is True
    assert intent_close.action == "application.close"
    assert intent_close.target == "Calculator"
    assert intent_close.risk_level == RiskLevel.MEDIUM

    # Check git status
    intent_git = parser.parse("check git status")
    assert intent_git.is_fast_path is True
    assert intent_git.action == "shell.execute"
    assert intent_git.parameters["command"] == "git status"


def test_goal_resolution():
    parser = IntentParser()
    resolver = GoalResolver()

    intent = parser.parse("Open Chrome")
    goal = resolver.resolve(intent)

    assert "application.open" in goal.description
    assert len(goal.success_conditions) >= 1
    assert goal.status == "PENDING"
