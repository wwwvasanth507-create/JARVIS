"""Unit tests for AmbiguityHandler and clarification flow."""

from jarvis.core.orchestration.ambiguity import AmbiguityCandidate, AmbiguityHandler, StructuredAmbiguity
from jarvis.core.orchestration.conversation_state import ConversationStateManager


def test_detect_ambiguity_candidates():
    state_mgr = ConversationStateManager()
    handler = AmbiguityHandler(state_mgr)

    candidates = ["C:\\Downloads\\report.pdf", "C:\\Documents\\report.pdf"]
    ambiguity = handler.check_file_search_ambiguity("report.pdf", candidates)

    assert isinstance(ambiguity, StructuredAmbiguity)
    assert len(ambiguity.candidates) == 2
    assert "Which one should I open, Boss?" in ambiguity.question


def test_clarification_preservation_and_resolution():
    state_mgr = ConversationStateManager()
    handler = AmbiguityHandler(state_mgr)

    candidates = ["C:\\Downloads\\report.pdf", "C:\\Documents\\report.pdf"]
    ambiguity = handler.check_file_search_ambiguity("report.pdf", candidates)
    handler.store_pending_clarification(ambiguity)

    assert handler.has_pending_clarification() is True

    resolved_cand = handler.resolve_pending_clarification("the first one")
    assert resolved_cand is not None
    assert resolved_cand.target_value == "C:\\Downloads\\report.pdf"
    assert handler.has_pending_clarification() is False
