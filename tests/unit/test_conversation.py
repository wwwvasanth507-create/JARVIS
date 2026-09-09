"""
Unit tests for ConversationManager and typed message objects.
"""

import pytest
from jarvis.brain.conversation import ConversationManager, UserMessage, AssistantMessage, SystemMessage
from jarvis.brain.context import ContextManager


def test_conversation_manager_add_messages():
    cm = ConversationManager(session_id="test_session")
    assert cm.message_count == 0

    user_msg = cm.add_user_message("Hello JARVIS", source="chat")
    assert isinstance(user_msg, UserMessage)
    assert user_msg.text == "Hello JARVIS"
    assert user_msg.source == "chat"
    assert cm.message_count == 1

    ast_msg = cm.add_assistant_message("Hello, Boss. How may I assist you?", duration_seconds=0.1, tokens_generated=8)
    assert isinstance(ast_msg, AssistantMessage)
    assert ast_msg.text == "Hello, Boss. How may I assist you?"
    assert cm.message_count == 2


def test_conversation_chat_history_conversion():
    cm = ConversationManager()
    cm.add_system_message("System prompt")
    cm.add_user_message("Hello")
    cm.add_assistant_message("Hi Boss")

    chat_history = cm.get_chat_history()
    assert len(chat_history) == 3
    assert chat_history[0].role == "system"
    assert chat_history[1].role == "user"
    assert chat_history[2].role == "assistant"


def test_conversation_clear():
    cm = ConversationManager()
    cm.add_user_message("Test")
    assert cm.message_count == 1
    cm.clear()
    assert cm.message_count == 0


def test_bounded_context_trimming():
    ctx_mgr = ContextManager(max_context_tokens=1500)
    cm = ConversationManager()

    for i in range(25):
        cm.add_user_message(f"User message number {i} with long detailed query about computer systems and tasks.")
        cm.add_assistant_message(f"Assistant response number {i} providing extensive detailed technical answers.")

    history = cm.get_chat_history()
    gen_req = ctx_mgr.build_generation_request(
        user_prompt="Latest request from Boss",
        history=history,
        max_response_tokens=200,
    )

    # Verify that total estimated tokens in trimmed messages fits within max_context_tokens budget
    total_tokens = sum(ctx_mgr.estimate_tokens(m.content) for m in gen_req.messages)
    assert total_tokens <= 1500
    # Verify that history was trimmed (fewer messages than original 50+ history)
    assert len(gen_req.messages) < len(history)
