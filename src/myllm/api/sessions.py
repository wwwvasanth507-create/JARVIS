"""
Session Registry and Concurrency Management for MyLLM API Server.

Maintains isolated ChatEngine instances per session with per-session asynchronous
locking to guarantee that concurrent requests never corrupt another session's
conversational history or KV cache.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
import uuid

from myllm.api.errors import MaxSessionsExceededError, SessionNotFoundError
from myllm.chat.engine import ChatEngine
from myllm.inference.types import GenerationConfig
from myllm.model.gpt import GPTModel
from myllm.tokenizer import Tokenizer

logger = logging.getLogger(__name__)


class SessionHandle:
    """
    Encapsulates state, engine, timestamps, and concurrency lock for a single session.
    """

    def __init__(
        self,
        session_id: str,
        engine: ChatEngine,
        system_prompt: Optional[str] = None,
        config: Optional[GenerationConfig] = None,
    ) -> None:
        self.session_id = session_id
        self.engine = engine
        self.system_prompt = system_prompt
        self.config = config or engine.default_config
        now_iso = datetime.now(timezone.utc).isoformat()
        self.created_at = now_iso
        self.updated_at = now_iso
        self.lock = asyncio.Lock()

    def touch(self) -> None:
        """Update last modified timestamp."""
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def cleanup(self) -> None:
        """Release underlying KV cache and clear conversational history."""
        self.engine.reset()


class SessionRegistry:
    """
    Thread-safe in-memory registry of active chat sessions.
    """

    def __init__(
        self,
        model: GPTModel,
        tokenizer: Tokenizer,
        max_sessions: int = 100,
        checkpoint_path: Optional[str] = None,
        default_config: Optional[GenerationConfig] = None,
    ) -> None:
        self.model = model
        self.tokenizer = tokenizer
        self.max_sessions = max_sessions
        self.checkpoint_path = checkpoint_path
        self.default_config = default_config
        self._sessions: Dict[str, SessionHandle] = {}
        self._registry_lock = asyncio.Lock()

    async def create_session(
        self,
        system_prompt: Optional[str] = None,
        generation_config: Optional[GenerationConfig] = None,
        custom_id: Optional[str] = None,
    ) -> SessionHandle:
        """
        Instantiate a new session with an isolated ChatEngine.
        """
        async with self._registry_lock:
            if len(self._sessions) >= self.max_sessions:
                raise MaxSessionsExceededError(self.max_sessions)

            session_id = custom_id or str(uuid.uuid4())
            cfg = generation_config or self.default_config

            # Create isolated ChatEngine sharing the read-only model weights & tokenizer
            engine = ChatEngine(
                model=self.model,
                tokenizer=self.tokenizer,
                system_prompt=system_prompt,
                default_config=cfg,
                checkpoint_path=self.checkpoint_path,
                device="cpu",
            )
            engine.session_id = session_id

            handle = SessionHandle(
                session_id=session_id,
                engine=engine,
                system_prompt=system_prompt,
                config=cfg,
            )
            self._sessions[session_id] = handle
            logger.info(f"Created chat session '{session_id}' (total active: {len(self._sessions)})")
            return handle

    async def get_session(self, session_id: str) -> SessionHandle:
        """Retrieve an active session handle or raise SessionNotFoundError."""
        async with self._registry_lock:
            handle = self._sessions.get(session_id)
            if handle is None:
                raise SessionNotFoundError(session_id)
            return handle

    async def delete_session(self, session_id: str) -> None:
        """Delete an active session and release its conversational state and KV cache."""
        async with self._registry_lock:
            handle = self._sessions.pop(session_id, None)
            if handle is None:
                raise SessionNotFoundError(session_id)
            handle.cleanup()
            logger.info(f"Deleted chat session '{session_id}' (remaining active: {len(self._sessions)})")

    async def list_session_ids(self) -> List[str]:
        """Return list of all active session IDs."""
        async with self._registry_lock:
            return list(self._sessions.keys())

    async def count(self) -> int:
        """Return number of active sessions."""
        async with self._registry_lock:
            return len(self._sessions)
