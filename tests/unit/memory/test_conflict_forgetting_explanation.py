"""
Unit tests for MemoryConflictResolver, UserCorrectionHandler, and MemoryExplanationEngine.
"""

import pytest
from jarvis.memory.memory_layers import ScopedPreference, MemoryScope, MemorySource, PreferenceLevel
from jarvis.memory.conflict_resolver import MemoryConflictResolver
from jarvis.memory.explanation_engine import MemoryExplanationEngine
from jarvis.memory.user_corrections import UserCorrectionHandler
from jarvis.memory.models import MemoryItem


def test_conflict_resolution_matrix():
    global_weak = ScopedPreference(
        key="browser",
        value="Chrome",
        level=PreferenceLevel.WEAK_INFERENCE,
        scope=MemoryScope.GLOBAL
    )
    project_explicit = ScopedPreference(
        key="browser",
        value="Firefox",
        level=PreferenceLevel.EXPLICIT,
        scope=MemoryScope.PROJECT
    )

    winner = MemoryConflictResolver.resolve_preference_conflict([global_weak, project_explicit])
    assert winner is not None
    assert winner.value == "Firefox"
    assert winner.scope == MemoryScope.PROJECT


def test_user_correction_handler_and_explanation():
    handler = UserCorrectionHandler()
    res = handler.parse_and_execute("Remember I use Firefox")
    assert res.is_correction is True
    assert res.action == "STORE_PREFERENCE"
    assert res.target_value == "firefox"

    mem = MemoryItem(key="preferred_browser", content="Firefox", source="USER_EXPLICIT")
    exp = MemoryExplanationEngine.explain_memory(mem)
    assert "explicitly told to me by you" in exp.explanation
