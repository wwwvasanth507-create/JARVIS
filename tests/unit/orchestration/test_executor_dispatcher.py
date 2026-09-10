"""
Unit tests for Executor, Dispatcher, and Confirmation handling.
"""

from jarvis.core.orchestration.confirmation import ConfirmationManager
from jarvis.core.orchestration.dispatcher import ToolDispatcher
from jarvis.core.orchestration.executor import PlanExecutor
from jarvis.core.orchestration.plan import Plan, PlanStep
from jarvis.core.orchestration.state import ExecutionState, ExecutionStatus
from jarvis.security.permissions import PermissionCategory, RiskLevel
from jarvis.tools.base import BaseTool, ToolMetadata, ToolResult


class DummyTool(BaseTool):
    def __init__(self):
        super().__init__(
            ToolMetadata(
                name="dummy.test_action",
                description="Dummy tool for testing",
                permission_requirement=PermissionCategory.SYSTEM_CONTROL,
                risk_level=RiskLevel.LOW,
            )
        )

    def execute(self, **kwargs):
        return ToolResult(success=True, data={"res": "ok"})

    def verify(self, execution_result, **kwargs):
        return True


def test_tool_dispatcher():
    dummy = DummyTool()
    dispatcher = ToolDispatcher(registry={"dummy.test_action": dummy})
    res = dispatcher.dispatch("dummy.test_action", {"param": 1})
    assert res.success is True
    assert res.data == {"res": "ok"}


def test_executor_confirmation_required():
    dummy = DummyTool()
    dispatcher = ToolDispatcher(registry={"dummy.test_action": dummy})
    conf_mgr = ConfirmationManager()
    executor = PlanExecutor(dispatcher=dispatcher, confirmation_mgr=conf_mgr)

    step = PlanStep(
        description="High risk operation",
        tool_name="dummy.test_action",
        risk_level=RiskLevel.HIGH,
        permission=PermissionCategory.SYSTEM_CONTROL,
    )
    plan = Plan(goal_id="g1", steps=[step])
    state = ExecutionState(execution_id="ex1", request="Do high risk")

    # 1. Execute without token -> should enter WAITING_FOR_CONFIRMATION
    res_state = executor.execute_plan(plan, state)
    assert res_state.status == ExecutionStatus.WAITING_FOR_CONFIRMATION
    token = res_state.confirmation_token
    assert token is not None

    # 2. Execute with valid token -> should complete execution
    res_state2 = executor.execute_plan(plan, state, confirmation_token=token)
    assert res_state2.status == ExecutionStatus.COMPLETED
