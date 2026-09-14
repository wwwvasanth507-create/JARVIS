"""
Chat Session serialization and persistence for MyLLM Chat Engine.

Stores conversational state, system prompts, message history, configuration,
and checkpoint identifiers in human-readable JSON format without pickle.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import uuid

from myllm.chat.message import ChatHistory, ChatMessage


class ChatSession:
    """
    Serializable container for a full conversational session.

    Attributes:
        session_id: Unique UUID identifier for this session.
        system_prompt: Optional overarching system directive.
        history: ChatHistory instance containing ordered messages.
        generation_config: Dictionary of inference parameters used.
        created_at: ISO-8601 UTC timestamp of creation.
        updated_at: ISO-8601 UTC timestamp of last update.
        model_checkpoint: Path or identifier of the associated model checkpoint.
        tokenizer_fingerprint: SHA-256 fingerprint of the tokenizer.
    """

    def __init__(
        self,
        session_id: Optional[str] = None,
        system_prompt: Optional[str] = None,
        history: Optional[ChatHistory] = None,
        generation_config: Optional[Dict[str, Any]] = None,
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None,
        model_checkpoint: Optional[str] = None,
        tokenizer_fingerprint: Optional[str] = None,
    ) -> None:
        now_iso = datetime.now(timezone.utc).isoformat()
        self.session_id = session_id or str(uuid.uuid4())
        self.system_prompt = system_prompt
        self.history = history if history is not None else ChatHistory()
        self.generation_config = generation_config or {}
        self.created_at = created_at or now_iso
        self.updated_at = updated_at or now_iso
        self.model_checkpoint = model_checkpoint
        self.tokenizer_fingerprint = tokenizer_fingerprint

    def add_message(self, role: str, content: str) -> ChatMessage:
        """Add a message and update timestamp."""
        msg = self.history.add_message(role=role, content=content)
        self.updated_at = datetime.now(timezone.utc).isoformat()
        return msg

    def to_dict(self) -> Dict[str, Any]:
        """Convert session to JSON-serializable dictionary."""
        return {
            "session_id": self.session_id,
            "system_prompt": self.system_prompt,
            "messages": self.history.to_list(),
            "generation_config": self.generation_config,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "model_checkpoint": self.model_checkpoint,
            "tokenizer_fingerprint": self.tokenizer_fingerprint,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ChatSession:
        """Construct a ChatSession from a dictionary."""
        if not isinstance(data, dict):
            raise TypeError(f"Expected dict for ChatSession, got {type(data).__name__}")

        raw_messages = data.get("messages", [])
        history = ChatHistory.from_list(raw_messages)

        return cls(
            session_id=data.get("session_id"),
            system_prompt=data.get("system_prompt"),
            history=history,
            generation_config=data.get("generation_config", {}),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            model_checkpoint=data.get("model_checkpoint"),
            tokenizer_fingerprint=data.get("tokenizer_fingerprint"),
        )

    def save_json(self, file_path: Union[str, Path]) -> Path:
        """Save session to a JSON file."""
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
        return path

    @classmethod
    def load_json(cls, file_path: Union[str, Path]) -> ChatSession:
        """Load session from a JSON file."""
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(f"Session file not found at: {path}")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)
