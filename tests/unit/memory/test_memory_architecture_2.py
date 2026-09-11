"""
Unit tests for 6-Layer Memory Architecture, Working Memory, and Preference Confidence Decay.
"""

import pytest
import time
from jarvis.memory.memory_layers import ScopedPreference, PreferenceLevel, MemoryScope, MemorySource
from jarvis.memory.working_memory import WorkingMemoryManager


def test_working_memory_session_lifecycle():
    wm = WorkingMemoryManager.get_instance()
    sess = wm.start_session("s1", "Prepare monthly report")
    assert sess.session_id == "s1"
    assert sess.current_request == "Prepare monthly report"

    wm.update_context(application="Chrome", file_path="report.pdf")
    active = wm.get_session()
    assert active.active_application == "Chrome"
    assert active.active_file == "report.pdf"

    wm.clear_session()
    assert wm._active_session is None


def test_preference_confidence_decay():
    p_inferred = ScopedPreference(
        key="browser",
        value="Firefox",
        level=PreferenceLevel.WEAK_INFERENCE,
        confidence=1.0,
        updated_at=time.time() - (60 * 86400.0)  # 60 days ago
    )
    decayed = p_inferred.get_decayed_confidence(half_life_days=30.0)
    assert decayed < 0.3  # Decayed significantly after 2 half lives

    p_explicit = ScopedPreference(
        key="browser",
        value="Firefox",
        level=PreferenceLevel.EXPLICIT,
        confidence=1.0,
        updated_at=time.time() - (60 * 86400.0)
    )
    assert p_explicit.get_decayed_confidence() == 1.0  # Explicit preferences do NOT decay
