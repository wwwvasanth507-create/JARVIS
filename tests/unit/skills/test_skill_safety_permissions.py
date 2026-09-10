"""
Unit tests for SkillSafetyPolicy risk escalation and SkillPermissionChecker.
"""

from jarvis.security.permissions import PermissionCategory, RiskLevel
from jarvis.skills.models import SkillCategory, SkillDefinition
from jarvis.skills.permissions import SkillPermissionChecker
from jarvis.skills.safety import SkillSafetyPolicy
from jarvis.tools.base import BaseTool, ToolMetadata, ToolResult


class HighRiskDummyTool(BaseTool):
    def __init__(self):
        super().__init__(
            ToolMetadata(
                name="high_risk.dummy_tool",
                description="High risk dummy tool",
                permission_requirement=PermissionCategory.RUN_COMMANDS,
                risk_level=RiskLevel.HIGH,
            )
        )

    def execute(self, **kwargs):
        return ToolResult(success=True)

    def verify(self, execution_result, **kwargs):
        return True


def test_safety_policy_escalates_risk():
    safety = SkillSafetyPolicy()
    dummy = HighRiskDummyTool()
    registry = {"high_risk.dummy_tool": dummy}

    skill = SkillDefinition(
        skill_id="low_skill",
        name="Low Skill",
        description="Declared low risk skill using high risk tool",
        category=SkillCategory.USER,
        tools=["high_risk.dummy_tool"],
        risk_level=RiskLevel.LOW,
    )

    eff_risk = safety.compute_effective_risk(skill, registry)
    assert eff_risk == RiskLevel.HIGH
    assert skill.effective_risk_level == RiskLevel.HIGH
