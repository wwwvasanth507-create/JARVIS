"""
Unit tests for Verification, Recovery, Loop Detection, and Cancellation.
"""

import pytest
from jarvis.core.orchestration.cancellation import CancellationManager
from jarvis.core.orchestration.dispatcher import ToolDispatcher
from jarvis.core.orchestration.errors import LoopDetectedError
from jarvis.core.orchestration.executor import PlanExecutor
from jarvis.core.orchestration.plan import Plan, PlanStep
from jarvis.core.orchestration.recovery import RecoveryManager
from jarvis.core.orchestration.state import ExecutionState, ExecutionStatus
from jarvis.core.orchestration.verification import VerificationManager
from jarvis.security.permissions import PermissionCategory, RiskLevel
from jarvis.tools.base import BaseTool, ToolMetadata, ToolResult


class FailingVerifyTool(BaseTool):
    def __init__(self):
        super().__init__(
            ToolMetadata(
                name="failing.verify_tool",
                description="Tool that executes but fails verification",
                permission_requirement=PermissionCategory.SYSTEM_CONTROL,
                risk_level=RiskLevel.LOW,
            )
        )

    def execute(self, **kwargs):
        return ToolResult(success=True, data="done")

    def verify(self, execution_result, **kwargs):
        return False


def test_verification_refuses_fake_success():
    tool = FailingVerifyTool()
    dispatcher = ToolDispatcher(registry={"failing.verify_tool": tool})
    executor = PlanExecutor(dispatcher=dispatcher)

    step = PlanStep(
        description="Failing verify step",
        tool_name="failing.verify_tool",
        risk_level=RiskLevel.LOW,
        permission=PermissionCategory.SYSTEM_CONTROL,
    )
    plan = Plan(goal_id="g1", steps=[step])
    state = ExecutionState(execution_id="ex1", request="Run failing verify")

    res_state = executor.execute_plan(plan, state)
    assert res_state.status == ExecutionStatus.FAILED
    assert "verification" in res_state.error.lower()


def test_loop_detection():
    recovery = RecoveryManager()
    recovery.track_action("tool.a", {"p": 1}, "err1")
    recovery.track_action("tool.a", {"p": 1}, "err1")
    with pytest.raises(LoopDetectedError):
        recovery.track_action("tool.a", {"p": 1}, "err1")


def test_cancellation_keywords():
    canceller = CancellationManager()
    assert canceller.is_cancellation_request("stop") is True
    assert canceller.is_cancellation_request("Cancel that!") is True
    assert canceller.is_cancellation_request("Open Chrome") is False
