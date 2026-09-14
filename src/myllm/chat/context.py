"""
Context Window Management for MyLLM Conversational Chat Engine.

Provides deterministic conversation history truncation to respect finite model
context lengths while preserving system prompt and the latest user query.
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple

from myllm.chat.message import ChatHistory, ChatMessage
from myllm.chat.template import ChatTemplate
from myllm.tokenizer.tokenizer import Tokenizer

logger = logging.getLogger(__name__)


@dataclass
class ContextInfo:
    """
    Diagnostic metadata regarding context window utilization and truncation.
    """

    total_tokens: int
    used_tokens: int
    truncated: bool
    removed_messages: int
    system_preserved: bool
    max_context_length: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert to serializable dictionary."""
        return asdict(self)


class ContextManager:
    """
    Manages conversational context truncation against a fixed token window.

    Strategy:
    1. Preserve the system prompt if present.
    2. Preserve the latest user message.
    3. Remove the oldest conversation turns (user/assistant pairs) first.
    4. Maintain valid role sequence integrity (no orphaned responses).
    5. Expose precise ContextInfo telemetry.
    """

    def __init__(
        self,
        tokenizer: Tokenizer,
        context_length: int,
        min_response_budget: int = 1,
    ) -> None:
        self.tokenizer = tokenizer
        self.context_length = context_length
        self.min_response_budget = min_response_budget

    def count_prompt_tokens(
        self,
        history: Sequence[ChatMessage],
        system_prompt: Optional[str] = None,
    ) -> int:
        """Serialize and count the exact token length of the conditioning prompt."""
        prompt_text = ChatTemplate.format_prompt(history, system_prompt=system_prompt)
        token_ids = self.tokenizer.encode(prompt_text, add_bos=False, add_eos=False)
        return len(token_ids)

    def fit_context(
        self,
        history: Sequence[ChatMessage],
        system_prompt: Optional[str] = None,
        max_new_tokens: int = 16,
    ) -> Tuple[List[ChatMessage], ContextInfo, str]:
        """
        Deterministically truncate history if needed so prompt + response budget fits.

        Args:
            history: Full message sequence.
            system_prompt: Optional system directive.
            max_new_tokens: Desired generation length.

        Returns:
            Tuple of (truncated_messages, ContextInfo, formatted_prompt_text).
        """
        # Desired budget for prompt:
        min_reserve = max(1, self.min_response_budget)
        reserve_tokens = max(min_reserve, min(max_new_tokens, self.context_length // 2))
        max_allowed_prompt_tokens = max(1, self.context_length - reserve_tokens)
        absolute_max_prompt_tokens = max(1, self.context_length - min_reserve)

        current_messages = list(history)
        initial_token_count = self.count_prompt_tokens(current_messages, system_prompt)

        if initial_token_count <= max_allowed_prompt_tokens or (
            len(current_messages) <= 1 and initial_token_count <= absolute_max_prompt_tokens
        ):
            prompt_text = ChatTemplate.format_prompt(current_messages, system_prompt)
            info = ContextInfo(
                total_tokens=self.context_length,
                used_tokens=initial_token_count,
                truncated=False,
                removed_messages=0,
                system_preserved=bool(system_prompt and system_prompt.strip()),
                max_context_length=self.context_length,
            )
            return current_messages, info, prompt_text

        # Truncation required:
        # We must keep the latest user message (last message) if possible.
        removed_count = 0
        system_preserved = bool(system_prompt and system_prompt.strip())

        # While prompt exceeds budget and we have more than 1 message in history:
        # Remove oldest message(s) from the front
        while len(current_messages) > 1:
            # Check if oldest is a user message followed by assistant
            # If so, remove the turn pair to preserve turn structure
            if len(current_messages) >= 2 and current_messages[0].role == "user" and current_messages[1].role == "assistant":
                current_messages.pop(0)
                current_messages.pop(0)
                removed_count += 2
            else:
                current_messages.pop(0)
                removed_count += 1

            curr_tokens = self.count_prompt_tokens(current_messages, system_prompt)
            if curr_tokens <= max_allowed_prompt_tokens:
                break

        curr_tokens = self.count_prompt_tokens(current_messages, system_prompt)

        # If even with a single message it still exceeds budget:
        # Check if dropping system prompt helps
        if curr_tokens > absolute_max_prompt_tokens and system_prompt:
            logger.warning("Prompt exceeds context length even with minimal history; dropping system prompt.")
            system_preserved = False
            system_prompt = None
            curr_tokens = self.count_prompt_tokens(current_messages, system_prompt=None)

        # If still exceeding absolute max allowed prompt tokens, truncate the latest message content
        if curr_tokens > absolute_max_prompt_tokens and current_messages:
            last_msg = current_messages[-1]
            empty_last = [ChatMessage(role=m.role, content=m.content) for m in current_messages[:-1]]
            empty_last.append(ChatMessage(role=last_msg.role, content=""))
            overhead_tokens = self.count_prompt_tokens(empty_last, system_prompt=system_prompt)
            content_token_budget = max(1, absolute_max_prompt_tokens - overhead_tokens)

            user_tokens = self.tokenizer.encode(last_msg.content, add_bos=False, add_eos=False)
            if len(user_tokens) > content_token_budget:
                trimmed_tokens = user_tokens[-content_token_budget:]
                trimmed_text = self.tokenizer.decode(trimmed_tokens).strip()
                if not trimmed_text:
                    trimmed_text = last_msg.content[:content_token_budget]
                current_messages[-1] = ChatMessage(role=last_msg.role, content=trimmed_text)
                curr_tokens = self.count_prompt_tokens(current_messages, system_prompt=system_prompt)

        prompt_text = ChatTemplate.format_prompt(current_messages, system_prompt=system_prompt)
        info = ContextInfo(
            total_tokens=self.context_length,
            used_tokens=curr_tokens,
            truncated=True,
            removed_messages=removed_count,
            system_preserved=system_preserved,
            max_context_length=self.context_length,
        )
        return current_messages, info, prompt_text
