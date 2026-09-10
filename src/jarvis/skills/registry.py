"""
Skill Registry for JARVIS.
"""

from typing import Dict, List, Optional
from jarvis.skills.errors import SkillNotFoundError
from jarvis.skills.lifecycle import SkillLifecycleManager
from jarvis.skills.models import SkillCategory, SkillDefinition, SkillLifecycleState, SkillQueryResult


class SkillRegistry:
    """Registry maintaining active skills, lookup tables, and enable/disable states."""

    def __init__(self, lifecycle_mgr: Optional[SkillLifecycleManager] = None):
        self._skills: Dict[str, SkillDefinition] = {}
        self._alias_map: Dict[str, str] = {}
        self.lifecycle_mgr = lifecycle_mgr or SkillLifecycleManager()

    def register(self, skill: SkillDefinition) -> None:
        self._skills[skill.skill_id] = skill
        for alias in skill.aliases:
            self._alias_map[alias.lower()] = skill.skill_id
        if skill.state == SkillLifecycleState.VALIDATED:
            self.lifecycle_mgr.enable(skill)

    def unregister(self, skill_id: str) -> bool:
        if skill_id in self._skills:
            skill = self._skills.pop(skill_id)
            for alias in skill.aliases:
                self._alias_map.pop(alias.lower(), None)
            return True
        return False

    def get(self, skill_id: str) -> Optional[SkillDefinition]:
        return self._skills.get(skill_id)

    def find_by_alias(self, alias: str) -> Optional[SkillDefinition]:
        sid = self._alias_map.get(alias.lower())
        if sid:
            return self.get(sid)
        return None

    def enable(self, skill_id: str) -> SkillDefinition:
        skill = self.get(skill_id)
        if not skill:
            raise SkillNotFoundError(f"Skill '{skill_id}' not found.")
        return self.lifecycle_mgr.enable(skill)

    def disable(self, skill_id: str) -> SkillDefinition:
        skill = self.get(skill_id)
        if not skill:
            raise SkillNotFoundError(f"Skill '{skill_id}' not found.")
        return self.lifecycle_mgr.disable(skill)

    def list_skills(
        self,
        category: Optional[SkillCategory] = None,
        enabled_only: bool = False,
    ) -> List[SkillDefinition]:
        res = []
        for s in self._skills.values():
            if category and s.category != category:
                continue
            if enabled_only and s.state != SkillLifecycleState.ENABLED:
                continue
            res.append(s)
        return res

    def list_query_results(self) -> List[SkillQueryResult]:
        return [
            SkillQueryResult(
                skill_id=s.skill_id,
                name=s.name,
                description=s.description,
                category=s.category,
                state=s.state,
                enabled=(s.state == SkillLifecycleState.ENABLED),
                risk_level=s.effective_risk_level or s.risk_level,
            )
            for s in self._skills.values()
        ]
