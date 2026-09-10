"""
Unit tests for SkillRegistry and SkillLoader.
"""

from jarvis.skills.discovery import SkillDiscovery
from jarvis.skills.loader import SkillLoader
from jarvis.skills.models import SkillLifecycleState
from jarvis.skills.registry import SkillRegistry
from jarvis.tools import ALL_TOOLS


def test_builtin_skills_loading():
    tools = {t.name: t for t in ALL_TOOLS}
    discovery = SkillDiscovery()
    loader = SkillLoader()
    registry = SkillRegistry()

    manifest_paths = discovery.discover_manifest_paths(["skills/builtin"])
    assert len(manifest_paths) >= 5

    for path in manifest_paths:
        skill = loader.load_skill(path, tools)
        registry.register(skill)

    loaded = registry.list_skills()
    assert len(loaded) >= 5

    # Test enable/disable
    sid = loaded[0].skill_id
    registry.disable(sid)
    assert registry.get(sid).state == SkillLifecycleState.DISABLED

    registry.enable(sid)
    assert registry.get(sid).state == SkillLifecycleState.ENABLED
