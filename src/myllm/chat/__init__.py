"""
Conversational Chat Engine for MyLLM (Phase 8).

Exports core chat components:
- ChatMessage: validated message abstraction (roles: system, user, assistant)
- ChatHistory: ordered conversation sequence
- ChatTemplate: deterministic multi-turn serialization format
- ContextManager & ContextInfo: deterministic turn-level context truncation
- ChatToken: streaming generation token container
- ChatTelemetry & ChatResponse: runtime generation diagnostics
- ChatSession: JSON-serializable persistent conversation state
- ChatEngine: multi-turn KV-cached conversation engine
"""

from myllm.chat.context import ContextInfo, ContextManager
from myllm.chat.engine import ChatEngine
from myllm.chat.message import ChatHistory, ChatMessage
from myllm.chat.session import ChatSession
from myllm.chat.telemetry import ChatResponse, ChatTelemetry, ChatToken
from myllm.chat.template import (
    CHAT_TEMPLATE_VERSION,
    ChatTemplate,
    sanitize_role_content,
    unescape_role_content,
)

__all__ = [
    "ChatMessage",
    "ChatHistory",
    "ChatTemplate",
    "CHAT_TEMPLATE_VERSION",
    "sanitize_role_content",
    "unescape_role_content",
    "ContextInfo",
    "ContextManager",
    "ChatToken",
    "ChatTelemetry",
    "ChatResponse",
    "ChatSession",
    "ChatEngine",
]
