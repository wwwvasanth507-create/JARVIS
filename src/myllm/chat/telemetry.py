"""
Telemetry and streaming types for MyLLM Chat Engine.

Defines ChatToken for streaming response generation and ChatTelemetry / ChatResponse
for structured runtime performance reporting.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional
from myllm.chat.context import ContextInfo
from myllm.chat.message import ChatMessage


@dataclass
class ChatToken:
    """
    A single token emitted during streaming response generation.

    Attributes:
        token_id: Integer token ID.
        text: Decoded string representation of this token.
        finished: True if this token concludes the generation.
        stop_reason: Reason for completion ('eos', 'max_new_tokens', 'context_limit', or None).
    """

    token_id: int
    text: str
    finished: bool = False
    stop_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ChatTelemetry:
    """
    Detailed performance metrics and diagnostics for a chat interaction.
    """

    prompt_tokens: int
    generated_tokens: int
    total_tokens: int
    generation_latency: float
    tokens_per_second: float
    stop_reason: str
    context_truncated: bool
    removed_messages: int
    cache_used: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ChatResponse:
    """
    Complete response container for a conversational turn.
    """

    message: ChatMessage
    telemetry: ChatTelemetry
    context_info: ContextInfo

    @property
    def content(self) -> str:
        """Convenience property for assistant response text."""
        return self.message.content

    def to_dict(self) -> Dict[str, Any]:
        return {
            "message": self.message.to_dict(),
            "telemetry": self.telemetry.to_dict(),
            "context_info": self.context_info.to_dict(),
        }
