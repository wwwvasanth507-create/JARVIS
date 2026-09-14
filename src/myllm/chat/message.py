"""
Message and history data structures for MyLLM Conversational Chat Engine.

Defines ChatMessage with strict role validation and ChatHistory for ordered
multi-turn conversation management.
"""

from __future__ import annotations

import copy
from dataclasses import asdict, dataclass
from typing import Any, Dict, Iterator, List, Optional, Sequence, Union

SUPPORTED_ROLES = {"system", "user", "assistant"}


@dataclass
class ChatMessage:
    """
    A single message in a conversational exchange.

    Attributes:
        role: One of 'system', 'user', or 'assistant'.
        content: Text content of the message.
    """

    role: str
    content: str

    def __post_init__(self) -> None:
        if not isinstance(self.role, str):
            raise TypeError(f"ChatMessage role must be a string, got {type(self.role).__name__}")
        norm_role = self.role.strip().lower()
        if norm_role not in SUPPORTED_ROLES:
            raise ValueError(
                f"Unsupported role '{self.role}'. Supported roles are: {sorted(SUPPORTED_ROLES)}"
            )
        self.role = norm_role

        if not isinstance(self.content, str):
            raise TypeError(f"ChatMessage content must be a string, got {type(self.content).__name__}")

        # Empty content policy:
        # 'user' and 'assistant' messages cannot be empty/whitespace-only.
        # 'system' message may be empty, though typically omitted if empty.
        stripped_content = self.content.strip()
        if self.role in {"user", "assistant"} and not stripped_content:
            raise ValueError(f"ChatMessage with role '{self.role}' cannot have empty content.")
        self.content = stripped_content

    def to_dict(self) -> Dict[str, str]:
        """Serialize message to dictionary."""
        return {
            "role": self.role,
            "content": self.content,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ChatMessage:
        """Create ChatMessage from a dictionary."""
        if not isinstance(data, dict):
            raise TypeError(f"Expected dict for ChatMessage, got {type(data).__name__}")
        if "role" not in data or "content" not in data:
            raise ValueError("ChatMessage dictionary must contain 'role' and 'content' keys.")
        return cls(role=str(data["role"]), content=str(data["content"]))


class ChatHistory:
    """
    Ordered sequence of ChatMessage objects representing a conversation thread.
    """

    def __init__(self, messages: Optional[Sequence[ChatMessage]] = None) -> None:
        self._messages: List[ChatMessage] = []
        if messages:
            for msg in messages:
                self.append(msg)

    def append(self, message: ChatMessage) -> None:
        """Append a validated ChatMessage to history."""
        if not isinstance(message, ChatMessage):
            raise TypeError(f"Expected ChatMessage instance, got {type(message).__name__}")
        self._messages.append(message)

    def add_message(self, role: str, content: str) -> ChatMessage:
        """Create and append a ChatMessage to history."""
        msg = ChatMessage(role=role, content=content)
        self.append(msg)
        return msg

    @property
    def messages(self) -> List[ChatMessage]:
        """Return a copy of the ordered messages list."""
        return list(self._messages)

    @property
    def last_message(self) -> Optional[ChatMessage]:
        """Return the most recent message in history, or None if empty."""
        return self._messages[-1] if self._messages else None

    def clear(self) -> None:
        """Remove all messages from history."""
        self._messages.clear()

    def clone(self) -> ChatHistory:
        """Return a deep copy of this ChatHistory."""
        return ChatHistory([copy.deepcopy(m) for m in self._messages])

    def to_list(self) -> List[Dict[str, str]]:
        """Serialize all messages to a list of dicts."""
        return [m.to_dict() for m in self._messages]

    @classmethod
    def from_list(cls, data: Sequence[Dict[str, Any]]) -> ChatHistory:
        """Deserialize from a sequence of message dicts."""
        if not isinstance(data, (list, tuple)):
            raise TypeError(f"Expected sequence of dicts, got {type(data).__name__}")
        return cls([ChatMessage.from_dict(d) for d in data])

    def __len__(self) -> int:
        return len(self._messages)

    def __getitem__(self, idx: Union[int, slice]) -> Union[ChatMessage, List[ChatMessage]]:
        return self._messages[idx]

    def __iter__(self) -> Iterator[ChatMessage]:
        return iter(self._messages)

    def __repr__(self) -> str:
        return f"ChatHistory(length={len(self._messages)}, messages={self._messages})"
