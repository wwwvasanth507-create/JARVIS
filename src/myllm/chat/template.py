"""
Deterministic conversation serialization template for MyLLM Chat Engine.

Provides ChatTemplate formatting compatible with Phase 7 instruction templates,
supporting optional system prompts, multi-turn history formatting, generation
conditioning prompts, and formatting isolation against role spoofing.
"""

from __future__ import annotations

import re
from typing import List, Optional, Sequence
from myllm.chat.message import ChatHistory, ChatMessage

CHAT_TEMPLATE_VERSION = "1.0"

# Role header definitions
HEADER_SYSTEM = "### System:"
HEADER_USER = "### User:"
HEADER_ASSISTANT = "### Assistant:"

ROLE_HEADERS = {
    "system": HEADER_SYSTEM,
    "user": HEADER_USER,
    "assistant": HEADER_ASSISTANT,
}

# Regex pattern for role injection detection/escaping
ROLE_HEADER_PATTERN = re.compile(r"^(###\s*(?:System|User|Assistant):)", re.MULTILINE | re.IGNORECASE)


def sanitize_role_content(content: str) -> str:
    """
    Format-isolate user content to prevent role spoofing.

    If the user text contains headers like '### System:', '### User:', or '### Assistant:',
    escape the leading '#' to '\\###' so that role boundaries are preserved.

    Note: This provides structural formatting isolation, not an adversarial security boundary.
    """
    return ROLE_HEADER_PATTERN.sub(r"\\\1", content)


def unescape_role_content(content: str) -> str:
    """Reverse the escaping applied by sanitize_role_content."""
    return re.sub(r"^\\(###\s*(?:System|User|Assistant):)", r"\1", content, flags=re.MULTILINE | re.IGNORECASE)


class ChatTemplate:
    """
    Deterministic conversation serializer for MyLLM.

    Format specification:
        ### System:
        {system_message}

        ### User:
        {user_message}

        ### Assistant:
        {assistant_message}

    When prompting the model to generate the next assistant response, the prompt ends with:
        ### Assistant:
    """

    VERSION = CHAT_TEMPLATE_VERSION

    @classmethod
    def format_message(cls, message: ChatMessage, sanitize: bool = True) -> str:
        """
        Format a single ChatMessage into its template block.

        Args:
            message: The message to format.
            sanitize: If True, sanitize content against accidental role header spoofing.
        """
        header = ROLE_HEADERS.get(message.role, f"### {message.role.capitalize()}:")
        content = sanitize_role_content(message.content) if sanitize else message.content
        return f"{header}\n{content}"

    @classmethod
    def format_conversation(
        cls,
        history: Sequence[ChatMessage],
        system_prompt: Optional[str] = None,
        sanitize: bool = True,
    ) -> str:
        """
        Format a complete multi-turn conversation into a deterministic text string.

        Args:
            history: Sequence of ChatMessage objects.
            system_prompt: Optional overarching system prompt.
            sanitize: Whether to escape role-spoofing markers in user content.
        """
        blocks: List[str] = []

        if system_prompt and system_prompt.strip():
            sys_msg = ChatMessage(role="system", content=system_prompt.strip())
            blocks.append(cls.format_message(sys_msg, sanitize=False))

        for msg in history:
            # Skip system messages embedded in history if we already handled system_prompt,
            # or include them if system_prompt wasn't provided
            if msg.role == "system":
                if not system_prompt or not system_prompt.strip():
                    blocks.append(cls.format_message(msg, sanitize=False))
            else:
                blocks.append(cls.format_message(msg, sanitize=sanitize))

        return "\n\n".join(blocks)

    @classmethod
    def format_prompt(
        cls,
        history: Sequence[ChatMessage],
        system_prompt: Optional[str] = None,
        sanitize: bool = True,
    ) -> str:
        """
        Format conversation history into a generation conditioning prompt.
        Appends the assistant header '### Assistant:\\n' to signal the model's turn.
        """
        conv_text = cls.format_conversation(
            history=history,
            system_prompt=system_prompt,
            sanitize=sanitize,
        )
        if conv_text:
            return f"{conv_text}\n\n{HEADER_ASSISTANT}\n"
        return f"{HEADER_ASSISTANT}\n"
