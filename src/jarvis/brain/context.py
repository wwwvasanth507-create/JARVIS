"""
Context Manager Subsystem for JARVIS.
Assembles system prompts, identity files, active conversation turns, and enforces prioritized context token budget protection.
"""

from pathlib import Path
from typing import List, Optional, Dict, Any
from jarvis.brain.models import ChatMessage, GenerationRequest


class ContextManager:
    """
    Manages prompt assembly and prioritized sliding-window context token budget protection.
    Priority Hierarchy:
    1. System / Security instructions
    2. Current user request
    3. Active tool contract
    4. Current execution state
    5. Relevant memory
    6. Relevant knowledge
    7. Recent conversation
    8. Older conversation
    """

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
        """Rough estimation: ~3.8 characters per token."""
        if not text:
            return 0
        return max(1, int(len(text) / 3.8))

    def build_generation_request(
        self,
        user_prompt: str,
        history: Optional[List[ChatMessage]] = None,
        tool_contract: Optional[str] = None,
        execution_state: Optional[str] = None,
        relevant_memory: Optional[List[str]] = None,
        relevant_knowledge: Optional[List[str]] = None,
        temperature: float = 0.2,
        max_response_tokens: int = 512,
    ) -> GenerationRequest:
        messages: List[ChatMessage] = []

        # Priority 1: System / Security instructions
        sys_instruction = self.full_system_instruction
        if tool_contract:
            sys_instruction += f"\n\nActive Tool Contract:\n{tool_contract}"
        if sys_instruction:
            messages.append(ChatMessage(role="system", content=sys_instruction))

        # Priority 4 & 5 & 6: Execution state, Memory, Knowledge
        context_additions = []
        if execution_state:
            context_additions.append(f"Current State: {execution_state}")
        if relevant_memory:
            context_additions.append("Relevant Memory:\n" + "\n".join(f"- {m}" for m in relevant_memory))
        if relevant_knowledge:
            context_additions.append("Relevant Knowledge:\n" + "\n".join(f"- {k}" for k in relevant_knowledge))

        if context_additions:
            messages.append(ChatMessage(role="system", content="\n\n".join(context_additions)))

        # Priority 7 & 8: Recent & Older Conversation History
        if history:
            messages.extend(history)

        # Priority 2: Current user request (placed last in prompt stream)
        messages.append(ChatMessage(role="user", content=user_prompt))

        # Calculate budget and trim lower-priority items first
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

        # Preserve System (first) and User request (last)
        has_system = messages[0].role == "system"
        sys_msg = messages[0] if has_system else None
        last_msg = messages[-1]

        preserved_tokens = (self.estimate_tokens(sys_msg.content) if sys_msg else 0) + self.estimate_tokens(last_msg.content)
        remaining_budget = max(100, target_budget - preserved_tokens)

        middle_messages = messages[1:-1] if has_system else messages[:-1]
        trimmed_middle: List[ChatMessage] = []
        current_tokens = 0

        # Trim older conversation history first before trimming memory/knowledge
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
