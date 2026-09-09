"""
Foundation Unit Test Suite for JARVIS Phase 1.
"""

from pathlib import Path
import pytest

from jarvis.core.config import JarvisConfig
from jarvis.security.permissions import (
    PermissionEvaluator,
    PermissionCategory,
    RiskLevel,
)
from jarvis.tools.base import BaseTool, ToolMetadata, ToolResult
from jarvis.brain.provider import (
    MockLocalModelProvider,
    ModelGenerationRequest,
)
from jarvis.brain.loop import (
    AgentLoopContext,
    AgentLoopTracker,
    AgentLoopStage,
)


class DummyTestTool(BaseTool):
    """Concrete Dummy Tool for Foundation Testing."""

    def execute(self, **kwargs) -> ToolResult:
        value = kwargs.get("input_val", 0)
        return ToolResult(success=True, data={"result": value * 2})

    def verify(self, execution_result: ToolResult, **kwargs) -> bool:
        return execution_result.success and execution_result.data is not None


def test_jarvis_config_default():
    config = JarvisConfig()
    assert config.system.name == "JARVIS"
    assert config.system.user_alias == "Boss"
    assert config.system.local_first is True
    assert config.system.allow_external_apis is False


def test_permission_evaluator(tmp_path):
    perm_file = tmp_path / "permissions.yaml"
    perm_file.write_text(
        """
categories:
  READ_FILES:
    default_risk: LOW
risk_levels:
  LOW:
    require_confirmation: false
  HIGH:
    require_confirmation: true
policies:
  prohibited_actions:
    - "disable_security"
""",
        encoding="utf-8",
    )

    evaluator = PermissionEvaluator(permissions_file=perm_file)

    # Test allowed low risk action
    res1 = evaluator.evaluate(PermissionCategory.READ_FILES, RiskLevel.LOW, "read_notes")
    assert res1.allowed is True
    assert res1.requires_boss_approval is False

    # Test allowed high risk action (requires Boss approval)
    res2 = evaluator.evaluate(PermissionCategory.RUN_COMMANDS, RiskLevel.HIGH, "execute_script")
    assert res2.allowed is True
    assert res2.requires_boss_approval is True

    # Test prohibited action
    res3 = evaluator.evaluate(PermissionCategory.SYSTEM_CONTROL, RiskLevel.CRITICAL, "disable_security")
    assert res3.allowed is False
    assert res3.requires_boss_approval is True


def test_base_tool_contract():
    meta = ToolMetadata(
        name="test.dummy",
        description="Dummy test tool",
        permission_requirement=PermissionCategory.READ_FILES,
        risk_level=RiskLevel.LOW,
    )
    tool = DummyTestTool(metadata=meta)
    assert tool.name == "test.dummy"

    res = tool.execute(input_val=21)
    assert res.success is True
    assert res.data["result"] == 42
    assert tool.verify(res) is True


def test_mock_local_model_provider():
    provider = MockLocalModelProvider()
    assert provider.is_ready() is False
    assert provider.initialize() is True
    assert provider.is_ready() is True

    req = ModelGenerationRequest(prompt="Hello JARVIS")
    resp = provider.generate(req)
    assert "At your service, Boss" in resp.text
    assert resp.tokens_generated > 0


def test_agent_loop_tracker():
    context = AgentLoopContext(request_id="req-001", user_prompt="Status update")
    tracker = AgentLoopTracker(context)

    assert tracker.context.stage == AgentLoopStage.USER_REQUEST
    tracker.transition_to(AgentLoopStage.UNDERSTAND)
    assert tracker.context.stage == AgentLoopStage.UNDERSTAND

    tracker.mark_completed("All systems operational, Boss.")
    assert tracker.context.is_completed is True
    assert tracker.context.stage == AgentLoopStage.RESPOND
    assert tracker.context.final_response == "All systems operational, Boss."
