"""
Context Manager Subsystem for JARVIS.
Assembles system prompts, identity files, active conversation turns, and enforces context token budget protection.
"""

from pathlib import Path
from typing import List, Optional
from jarvis.brain.provider import ChatMessage, GenerationRequest


class ContextManager:
    """Manages prompt assembly and sliding-window context token budget protection."""

    def __init__(
        self,
        system_prompt_path: str = "prompts/system/jarvis_system.md",
        identity_dir: str = "prompts/identity",
        max_context_tokens: int = 2048,
    ):
        self.system_prompt_path = Path(system_prompt_path)
        self.identity_dir = Path(identity_dir)
        self.max_context_tokens = max_context_tokens
        self._system_prompt_text = ""
        self._identity_text = ""
        self._load_prompts()

    def _load_prompts(self) -> None:
        if self.system_prompt_path.exists():
            self._system_prompt_text = self.system_prompt_path.read_text(encoding="utf-8").strip()

        identity_files = ["identity.md", "personality.md", "boss_relationship.md"]
        combined_identity = []
        for fname in identity_files:
            fpath = self.identity_dir / fname
            if fpath.exists():
                combined_identity.append(fpath.read_text(encoding="utf-8").strip())
        self._identity_text = "\n\n".join(combined_identity)

    @property
    def full_system_instruction(self) -> str:
        parts = []
        if self._system_prompt_text:
            parts.append(self._system_prompt_text)
        if self._identity_text:
            parts.append(self._identity_text)
        return "\n\n---\n\n".join(parts)

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """Rough estimation: ~4 characters per token or word count * 1.3."""
        if not text:
            return 0
        return max(1, int(len(text) / 3.8))

    def build_generation_request(
        self,
        user_prompt: str,
        history: Optional[List[ChatMessage]] = None,
        temperature: float = 0.2,
        max_response_tokens: int = 512,
    ) -> GenerationRequest:
        messages: List[ChatMessage] = []

        # System message
        sys_instruction = self.full_system_instruction
        if sys_instruction:
            messages.append(ChatMessage(role="system", content=sys_instruction))

        # Add history
        if history:
            messages.extend(history)

        # Add latest user prompt
        messages.append(ChatMessage(role="user", content=user_prompt))

        # Calculate budget
        target_budget = self.max_context_tokens - max_response_tokens
        trimmed_messages = self._trim_to_budget(messages, target_budget)

        return GenerationRequest(
            messages=trimmed_messages,
            prompt=user_prompt,
            system_prompt=sys_instruction,
            temperature=temperature,
            max_tokens=max_response_tokens,
        )

    def _trim_to_budget(self, messages: List[ChatMessage], target_budget: int) -> List[ChatMessage]:
        if not messages:
            return []

        total_tokens = sum(self.estimate_tokens(m.content) for m in messages)
        if total_tokens <= target_budget:
            return messages

        # Preserve system prompt (message index 0 if role == 'system') and latest user message (last index)
        has_system = messages[0].role == "system"
        sys_msg = messages[0] if has_system else None
        last_msg = messages[-1]

        preserved_tokens = (self.estimate_tokens(sys_msg.content) if sys_msg else 0) + self.estimate_tokens(last_msg.content)

        remaining_budget = max(100, target_budget - preserved_tokens)
        middle_messages = messages[1:-1] if has_system else messages[:-1]

        trimmed_middle: List[ChatMessage] = []
        current_tokens = 0

        # Include recent history backwards within remaining budget
        for msg in reversed(middle_messages):
            msg_tokens = self.estimate_tokens(msg.content)
            if current_tokens + msg_tokens <= remaining_budget:
                trimmed_middle.insert(0, msg)
                current_tokens += msg_tokens
            else:
                break

        res = []
        if sys_msg:
            res.append(sys_msg)
        res.extend(trimmed_middle)
        res.append(last_msg)

        return res
