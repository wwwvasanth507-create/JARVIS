"""Unit tests for ClipboardController, PrivacyDashboardManager, and ActionJournal."""

import pytest
from jarvis.computer.clipboard import ClipboardController
from jarvis.system.privacy_dashboard import PrivacyDashboardManager
from jarvis.observability.action_journal import ActionJournal


def test_clipboard_credential_redaction():
    text_with_key = "api_key = 'secret_1234567890abcdef1234567890abcdef'"
    ClipboardController.set_text(text_with_key)

    info = ClipboardController.inspect()
    assert info["contains_potential_credential"] is True


def test_privacy_dashboard_states():
    mgr = PrivacyDashboardManager()
    states = mgr.get_privacy_states()

    assert "microphone" in states
    assert "screen_access" in states
    assert states["microphone"].enabled is True

    mgr.update_capability_state("microphone", False, "User muted microphone")
    assert mgr.get_privacy_states()["microphone"].enabled is False


def test_action_journal_secret_masking():
    journal = ActionJournal()
    entry = journal.log_action("WORKFLOW", "Updated config with api_key = 'secret123'")

    assert "secret123" not in entry.summary
    assert "[REDACTED]" in entry.summary
