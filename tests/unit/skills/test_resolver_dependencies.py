"""
Unit tests for SkillResolver and Ambiguity Detection.
"""

from jarvis.core.orchestration.intent import Intent, IntentConfidence
from jarvis.skills.models import SkillCategory, SkillDefinition, SkillLifecycleState
from jarvis.skills.registry import SkillRegistry
from jarvis.skills.resolver import SkillResolver


def test_resolver_intent_and_alias():
    registry = SkillRegistry()
    skill = SkillDefinition(
        skill_id="test_open_app",
        name="Test Open App",
        description="Test description",
        category=SkillCategory.BUILTIN,
        aliases=["start application"],
        intents=["application.open"],
        tools=["application.open"],
        state=SkillLifecycleState.ENABLED,
    )
    registry.register(skill)
    resolver = SkillResolver(registry)

    # 1. Resolve via intent
    intent = Intent(action="application.open", confidence=IntentConfidence.HIGH)
    res = resolver.resolve_intent(intent)
    assert res is not None
    assert res.skill_id == "test_open_app"

    # 2. Resolve via alias
    intent_alias = Intent(action="unknown", target="start application")
    res_alias = resolver.resolve_intent(intent_alias)
    assert res_alias is not None
    assert res_alias.skill_id == "test_open_app"
