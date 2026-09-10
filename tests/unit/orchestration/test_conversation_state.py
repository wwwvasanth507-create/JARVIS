"""
Unit tests for Conversation State Manager.
"""

from jarvis.core.orchestration.conversation_state import ConversationStateManager, ConversationState


def test_conversation_state_recording():
    mgr = ConversationStateManager()
    mgr.reset()
    state = mgr.state

    state.record_entity("sales_report", "file", "C:/docs/sales.pdf")
    latest_file = state.get_latest_entity("file")
    assert latest_file is not None
    assert latest_file.value == "C:/docs/sales.pdf"

    state.record_tool_output("filesystem.read_file", "Read file", "Sample text", status="SUCCESS")
    assert len(state.recent_tool_outputs) == 1
    assert state.recent_tool_outputs[0]["tool_name"] == "filesystem.read_file"

    mgr.reset()
    assert state.active_file is None
    assert len(state.active_entities) == 0
