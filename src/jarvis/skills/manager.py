"""
Central SkillManager Facade for JARVIS Modular Skill Subsystem.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
from jarvis.core.orchestration.intent import Intent
from jarvis.skills.discovery import SkillDiscovery
from jarvis.skills.errors import SkillDisabledError, SkillNotFoundError
from jarvis.skills.loader import SkillLoader
from jarvis.skills.models import SkillCategory, SkillDefinition, SkillLifecycleState, SkillQueryResult
from jarvis.skills.permissions import SkillPermissionChecker
from jarvis.skills.registry import SkillRegistry
from jarvis.skills.resolver import SkillResolver
class SkillManager:
    """Central Skill Subsystem facade coordinating discovery, registry, resolver, and execution."""

    def __init__(
        self,
        tool_registry: Optional[Dict[str, Any]] = None,
        skill_dirs: Optional[List[str]] = None,
    ):
        if tool_registry is not None:
            self.tools = tool_registry
        else:
            from jarvis.tools import ALL_TOOLS
            self.tools = {t.name: t for t in ALL_TOOLS}

        self.discovery = SkillDiscovery()
        self.loader = SkillLoader()
        self.registry = SkillRegistry()
        self.resolver = SkillResolver(self.registry)
        self.permission_checker = SkillPermissionChecker()
        self.skill_dirs = skill_dirs or SkillDiscovery.DEFAULT_DIRS

        # Discover & auto-load installed skill manifests
        self.discover_and_load_all()

    def discover_and_load_all(self) -> int:
        manifest_paths = self.discovery.discover_manifest_paths(self.skill_dirs)
        loaded_count = 0

        for path in manifest_paths:
            try:
                skill = self.loader.load_skill(path, self.tools)
                if skill.state in (SkillLifecycleState.VALIDATED, SkillLifecycleState.DISABLED):
                    self.registry.register(skill)
                    loaded_count += 1
            except Exception:
                pass

        return loaded_count

    def resolve_skill(self, intent: Intent) -> Optional[SkillDefinition]:
        return self.resolver.resolve_intent(intent)

    def enable_skill(self, skill_id: str) -> SkillDefinition:
        skill = self.registry.enable(skill_id)
        # Verify permission intersection
        self.permission_checker.check_skill_permissions(skill, self.tools)
        return skill

    def disable_skill(self, skill_id: str) -> SkillDefinition:
        return self.registry.disable(skill_id)

    def get_skill(self, skill_id: str) -> Optional[SkillDefinition]:
        return self.registry.get(skill_id)

    def list_skills(
        self,
        category: Optional[SkillCategory] = None,
        enabled_only: bool = False,
    ) -> List[SkillDefinition]:
        return self.registry.list_skills(category=category, enabled_only=enabled_only)

    def list_query_results(self) -> List[SkillQueryResult]:
        return self.registry.list_query_results()
