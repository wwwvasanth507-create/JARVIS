"""
Skill Lifecycle Manager for JARVIS.
"""

import time
from jarvis.skills.models import SkillDefinition, SkillLifecycleState


class SkillLifecycleManager:
    """Manages skill state transitions."""

    def enable(self, skill: SkillDefinition) -> SkillDefinition:
        if skill.state in (SkillLifecycleState.UNAVAILABLE, SkillLifecycleState.FAILED):
            return skill
        skill.state = SkillLifecycleState.ENABLED
        skill.enabled_at = time.time()
        return skill

    def disable(self, skill: SkillDefinition) -> SkillDefinition:
        skill.state = SkillLifecycleState.DISABLED
        return skill

    def mark_failed(self, skill: SkillDefinition, reason: str = "") -> SkillDefinition:
        skill.state = SkillLifecycleState.FAILED
        return skill
