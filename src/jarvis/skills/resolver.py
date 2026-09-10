"""
Skill Resolver for JARVIS.
"""

from typing import List, Optional
from jarvis.core.orchestration.intent import Intent
from jarvis.skills.errors import AmbiguousSkillError, SkillDisabledError
from jarvis.skills.models import SkillDefinition, SkillLifecycleState
from jarvis.skills.registry import SkillRegistry


class SkillResolver:
    """Resolves Intent objects and natural language queries to matching Skill definitions."""

    def __init__(self, registry: SkillRegistry):
        self.registry = registry

    def resolve_intent(self, intent: Intent) -> Optional[SkillDefinition]:
        candidates: List[SkillDefinition] = []
        action = intent.action
        target = (intent.target or "").lower()

        enabled_skills = self.registry.list_skills(enabled_only=True)

        # 1. Direct intent match
        for s in enabled_skills:
            if action in s.intents:
                candidates.append(s)

        # 2. Alias match
        if not candidates and target:
            alias_match = self.registry.find_by_alias(target)
            if alias_match and alias_match.state == SkillLifecycleState.ENABLED:
                candidates.append(alias_match)

        # 3. Tool capability match
        if not candidates:
            for s in enabled_skills:
                if action in s.tools:
                    candidates.append(s)

        if not candidates:
            return None

        if len(candidates) > 1:
            # If candidates contain both exact alias/intent match, filter
            exact = [c for c in candidates if action in c.intents or target in [a.lower() for a in c.aliases]]
            if len(exact) == 1:
                return exact[0]
            elif len(exact) > 1:
                c_names = [c.name for c in exact]
                raise AmbiguousSkillError(
                    f"Multiple matching skills found for intent '{action}': {c_names}",
                    candidates=c_names,
                )

        return candidates[0]
