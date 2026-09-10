"""
Skill Safety Policy & Effective Risk Escalation for JARVIS.
"""

from typing import Any, Dict
from jarvis.security.permissions import RiskLevel
from jarvis.skills.models import SkillDefinition


class SkillSafetyPolicy:
    """Escalates skill risk level based on underlying tool requirements."""

    RISK_HIERARCHY = {
        RiskLevel.LOW: 1,
        RiskLevel.MEDIUM: 2,
        RiskLevel.HIGH: 3,
        RiskLevel.CRITICAL: 4,
    }

    HIERARCHY_TO_RISK = {
        1: RiskLevel.LOW,
        2: RiskLevel.MEDIUM,
        3: RiskLevel.HIGH,
        4: RiskLevel.CRITICAL,
    }

    def compute_effective_risk(self, skill: SkillDefinition, tool_registry: Dict[str, Any]) -> RiskLevel:
        max_rank = self.RISK_HIERARCHY.get(skill.risk_level, 1)

        for tool_name in skill.tools:
            tool_obj = tool_registry.get(tool_name)
            if tool_obj and hasattr(tool_obj, "metadata"):
                t_rank = self.RISK_HIERARCHY.get(tool_obj.metadata.risk_level, 1)
                if t_rank > max_rank:
                    max_rank = t_rank

        for step in skill.workflow:
            tool_obj = tool_registry.get(step.action)
            if tool_obj and hasattr(tool_obj, "metadata"):
                t_rank = self.RISK_HIERARCHY.get(tool_obj.metadata.risk_level, 1)
                if t_rank > max_rank:
                    max_rank = t_rank

        effective = self.HIERARCHY_TO_RISK[max_rank]
        skill.effective_risk_level = effective
        return effective
