"""Unit tests for ReferenceResolver in JARVIS context engine."""

from jarvis.core.orchestration.conversation_state import ConversationStateManager
from jarvis.core.orchestration.reference_resolver import ReferenceResolver


def test_reference_resolver_pronoun():
    state_mgr = ConversationStateManager()
    state_mgr.record_tool_output("filesystem.search", "search", {"path": "C:\\docs\\sales_report.pdf"})

    resolver = ReferenceResolver(state_mgr)
    result = resolver.resolve("open it")

    assert "C:\\docs\\sales_report.pdf" in result.resolved_text


def test_reference_resolver_ordinal():
    state_mgr = ConversationStateManager()
    state_mgr.record_tool_output(
        "browser.search",
        "search",
        {
            "query": "A.R. Rahman songs",
            "results": [
                {"title": "Song 1", "url": "https://youtube.com/watch?v=1"},
                {"title": "Song 2", "url": "https://youtube.com/watch?v=2"},
                {"title": "Song 3", "url": "https://youtube.com/watch?v=3"},
            ],
        },
    )

    resolver = ReferenceResolver(state_mgr)
    result = resolver.resolve("play the second one")

    assert "https://youtube.com/watch?v=2" in result.resolved_text or "Song 2" in result.resolved_text


def test_reference_resolver_no_reference():
    state_mgr = ConversationStateManager()
    resolver = ReferenceResolver(state_mgr)

    text = "Open Chrome browser"
    result = resolver.resolve(text)
    assert result.resolved_text == text
