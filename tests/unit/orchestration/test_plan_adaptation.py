"""Unit tests for PlanQualityScorer, bounded conditional steps, and loop defense."""

from jarvis.core.orchestration.plan import Plan, PlanStep
from jarvis.core.orchestration.planner import PlanQualityScorer
from jarvis.core.orchestration.observation import ObservationManager
from jarvis.security.permissions import RiskLevel, PermissionCategory
from jarvis.tools.base import ToolResult


def test_plan_quality_scorer():
    good_step = PlanStep(
        step_id="step_1",
        tool_name="browser.open",
        arguments={"url": "https://google.com"},
        description="Open browser",
        risk_level=RiskLevel.LOW,
        permission=PermissionCategory.BROWSER_CONTROL,
    )
    plan = Plan(plan_id="plan_1", goal_id="goal_1", steps=[good_step])

    scoring = PlanQualityScorer.score_plan(plan)
    assert scoring["valid"] is True
    assert scoring["score"] >= 0.7


def test_plan_quality_scorer_rejects_unspecified_tool():
    unspecified_step = PlanStep(
        step_id="step_1",
        tool_name="general.task",
        arguments={},
        description="Generic task step",
        risk_level=RiskLevel.HIGH,
    )
    plan = Plan(plan_id="plan_1", goal_id="goal_2", steps=[unspecified_step])

    scoring = PlanQualityScorer.score_plan(plan)
    assert scoring["score"] < 1.0
    assert any("unspecified or generic tool" in reason for reason in scoring["reasons"])


def test_plan_loop_defense():
    obs_mgr = ObservationManager()
    dummy_res = ToolResult(success=True, data={})

    obs_mgr.observe("filesystem.search", {"query": "test"}, dummy_res)
    obs_mgr.observe("filesystem.search", {"query": "test"}, dummy_res)
    obs_mgr.observe("filesystem.search", {"query": "test"}, dummy_res)

    is_loop = obs_mgr.detect_semantic_loop("filesystem.search", {"query": "test"}, max_allowed=3)
    assert is_loop is True
