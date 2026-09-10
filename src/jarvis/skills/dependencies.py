"""
Skill Dependency Manager for JARVIS.
"""

from typing import Any, Dict, List
from jarvis.skills.models import SkillDefinition, SkillLifecycleState


class SkillDependencyManager:
    """Validates runtime subsystem and tool dependencies for skills."""

    def evaluate_dependencies(
        self,
        skill: SkillDefinition,
        available_tools: Dict[str, Any],
    ) -> tuple[bool, List[str]]:
        missing = []

        for tool_name in skill.tools:
            if tool_name not in available_tools:
                missing.append(f"tool:{tool_name}")

        for step in skill.workflow:
            if step.action not in available_tools and f"tool:{step.action}" not in missing:
                missing.append(f"tool:{step.action}")

        if missing:
            skill.state = SkillLifecycleState.UNAVAILABLE
            return False, missing

        return True, []
