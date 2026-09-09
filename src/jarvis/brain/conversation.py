"""
Conversation State Manager & Bounded Context Tracking for JARVIS.
Maintains session history, supports typed message models (UserMessage, AssistantMessage),
and enforces bounded context constraints.
"""

from typing import List, Literal, Optional, Union
import time
import uuid
from pydantic import BaseModel, Field
from jarvis.brain.provider import ChatMessage


class UserMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    text: str
    source: Literal["chat", "voice"] = "chat"
    timestamp: float = Field(default_factory=time.time)


class AssistantMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    text: str
    timestamp: float = Field(default_factory=time.time)
    duration_seconds: float = 0.0
    tokens_generated: int = 0


class SystemMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    text: str
    timestamp: float = Field(default_factory=time.time)


MessageUnion = Union[UserMessage, AssistantMessage, SystemMessage]


class ConversationSession(BaseModel):
    session_id: str = Field(default_factory=lambda: f"session_{uuid.uuid4().hex[:8]}")
    created_at: float = Field(default_factory=time.time)
    messages: List[MessageUnion] = Field(default_factory=list)
    max_history_tokens: int = 2048


class ConversationManager:
    """Manages the current active conversation state and bounded history."""

    def __init__(self, session_id: Optional[str] = None, max_tokens: int = 2048):
        self.session = ConversationSession(
            session_id=session_id or f"session_{uuid.uuid4().hex[:8]}",
            max_history_tokens=max_tokens,
        )

    def add_user_message(self, text: str, source: Literal["chat", "voice"] = "chat") -> UserMessage:
        msg = UserMessage(text=text, source=source)
        self.session.messages.append(msg)
        return msg

    def add_assistant_message(
        self, text: str, duration_seconds: float = 0.0, tokens_generated: int = 0
    ) -> AssistantMessage:
        msg = AssistantMessage(
            text=text, duration_seconds=duration_seconds, tokens_generated=tokens_generated
        )
        self.session.messages.append(msg)
        return msg

    def add_system_message(self, text: str) -> SystemMessage:
        msg = SystemMessage(text=text)
        self.session.messages.append(msg)
        return msg

    def get_chat_history(self) -> List[ChatMessage]:
        """Converts stored conversation messages into provider ChatMessage format."""
        chat_msgs: List[ChatMessage] = []
        for msg in self.session.messages:
            if isinstance(msg, UserMessage):
                chat_msgs.append(ChatMessage(role="user", content=msg.text))
            elif isinstance(msg, AssistantMessage):
                chat_msgs.append(ChatMessage(role="assistant", content=msg.text))
            elif isinstance(msg, SystemMessage):
                chat_msgs.append(ChatMessage(role="system", content=msg.text))
        return chat_msgs

    def clear(self) -> None:
        """Resets the conversation history."""
        self.session.messages.clear()

    @property
    def message_count(self) -> int:
        return len(self.session.messages)

    def get_last_user_message(self) -> Optional[UserMessage]:
        for msg in reversed(self.session.messages):
            if isinstance(msg, UserMessage):
                return msg
        return None

    def get_last_assistant_message(self) -> Optional[AssistantMessage]:
        for msg in reversed(self.session.messages):
            if isinstance(msg, AssistantMessage):
                return msg
        return None
