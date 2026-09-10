"""
Skill Permission Evaluator and Privilege Intersection for JARVIS.
"""

from typing import Any, Dict, Optional
from jarvis.security.permissions import PermissionEvaluator, PermissionCheckResult, RiskLevel
from jarvis.skills.errors import SkillPermissionDeniedError
from jarvis.skills.models import SkillDefinition


class SkillPermissionChecker:
    """Evaluates skill permissions under user intersection rules."""

    def __init__(self, evaluator: Optional[PermissionEvaluator] = None):
        self.evaluator = evaluator or PermissionEvaluator()

    def check_skill_permissions(
        self,
        skill: SkillDefinition,
        tool_registry: Dict[str, Any],
    ) -> PermissionCheckResult:
        # Check permissions for all declared tools in skill
        for tool_name in skill.tools:
            tool_obj = tool_registry.get(tool_name)
            if tool_obj and hasattr(tool_obj, "metadata"):
                res = self.evaluator.evaluate(
                    category=tool_obj.metadata.permission_requirement,
                    risk_level=tool_obj.metadata.risk_level,
                    action_name=tool_name,
                )
                if not res.allowed:
                    raise SkillPermissionDeniedError(
                        f"Skill '{skill.skill_id}' denied: tool '{tool_name}' rejected by security policy."
                    )

        # Skill passes intersection check
        return PermissionCheckResult(
            allowed=True,
            risk_level=skill.effective_risk_level or skill.risk_level,
            requires_boss_approval=(skill.effective_risk_level or skill.risk_level) in (RiskLevel.HIGH, RiskLevel.CRITICAL),
            reason=f"Skill '{skill.skill_id}' validated under security policy.",
        )
