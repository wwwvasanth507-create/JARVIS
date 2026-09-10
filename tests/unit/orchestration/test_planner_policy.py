"""
Unit tests for Planner and Policy Validator.
"""

import pytest
from jarvis.core.orchestration.errors import PlanValidationError
from jarvis.core.orchestration.goals import GoalResolver
from jarvis.core.orchestration.intent import IntentParser
from jarvis.core.orchestration.plan import Plan, PlanStep
from jarvis.core.orchestration.planner import Planner
from jarvis.core.orchestration.policy import PlanValidator
from jarvis.security.permissions import PermissionCategory, RiskLevel


def test_planner_fast_path_plan():
    parser = IntentParser()
    resolver = GoalResolver()
    planner = Planner()

    intent = parser.parse("Open Chrome")
    goal = resolver.resolve(intent)
    plan = planner.create_plan(intent, goal)

    assert len(plan.steps) == 1
    assert plan.steps[0].tool_name == "application.open"
    assert plan.steps[0].arguments == {"application": "Chrome"}


def test_validator_rejects_unregistered_tool():
    validator = PlanValidator()
    plan = Plan(
        goal_id="g1",
        steps=[
            PlanStep(
                description="Invalid step",
                tool_name="nonexistent.tool",
                risk_level=RiskLevel.LOW,
                permission=PermissionCategory.SYSTEM_CONTROL,
            )
        ],
    )
    with pytest.raises(PlanValidationError) as excinfo:
        validator.validate(plan, available_tools={"application.open": None})
    assert "registered" in str(excinfo.value)


def test_validator_prohibited_sequence():
    validator = PlanValidator()
    plan = Plan(
        goal_id="g1",
        steps=[
            PlanStep(
                description="Read file",
                tool_name="filesystem.read_file",
                risk_level=RiskLevel.LOW,
                permission=PermissionCategory.READ_FILES,
            ),
            PlanStep(
                description="Execute shell",
                tool_name="shell.execute",
                risk_level=RiskLevel.HIGH,
                permission=PermissionCategory.RUN_COMMANDS,
            ),
        ],
    )
    tools = {"filesystem.read_file": None, "shell.execute": None}
    with pytest.raises(PlanValidationError) as excinfo:
        validator.validate(plan, available_tools=tools)
    assert "Prohibited tool combination" in str(excinfo.value)
