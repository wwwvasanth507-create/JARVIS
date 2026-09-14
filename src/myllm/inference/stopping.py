"""
Stopping conditions and context validation for autoregressive generation.
"""

from __future__ import annotations

from typing import List, Optional, Tuple


class ContextOverflowError(ValueError):
    """Raised when prompt length plus requested tokens exceeds model context length."""


def check_eos(
    token_id: int,
    eos_token_id: Optional[int],
    stop_on_eos: bool = True,
) -> bool:
    """
    Check if the newly generated token triggers an EOS stop.

    Args:
        token_id: The integer ID of the generated token.
        eos_token_id: The designated EOS token ID, if configured.
        stop_on_eos: Whether EOS stopping is enabled.

    Returns:
        True if generation should terminate due to EOS.
    """
    if not stop_on_eos or eos_token_id is None:
        return False
    return token_id == eos_token_id


def validate_and_truncate_context(
    prompt_ids: List[int],
    max_new_tokens: int,
    context_length: int,
    strategy: str = "error",
) -> Tuple[List[int], int]:
    """
    Ensure the sequence fits within the model's fixed context window.

    If prompt_length + max_new_tokens > context_length:
    - If strategy == "error": raises ContextOverflowError.
    - If strategy == "truncate_prompt": preserves the most recent prompt tokens
      (left-truncation / dropping oldest tokens from the beginning) such that
      truncated_prompt_length + max_new_tokens <= context_length.
      If max_new_tokens >= context_length, at least 1 prompt token is kept and
      effective max_new_tokens is adjusted to context_length - len(truncated_prompt).

    Args:
        prompt_ids: Token IDs of the initial prompt.
        max_new_tokens: Number of tokens requested to generate.
        context_length: Maximum sequence length supported by the model.
        strategy: 'error' or 'truncate_prompt'.

    Returns:
        Tuple of (effective_prompt_ids, effective_max_new_tokens).

    Raises:
        ContextOverflowError: If overflow occurs under 'error' strategy.
        ValueError: If prompt is empty or context_length <= 0.
    """
    prompt_len = len(prompt_ids)
    if prompt_len == 0:
        raise ValueError("Prompt cannot be empty (0 tokens).")
    if context_length <= 0:
        raise ValueError(f"context_length must be positive, got {context_length}")

    if prompt_len > context_length:
        if strategy == "error":
            raise ContextOverflowError(
                f"Prompt length ({prompt_len}) exceeds model context length ({context_length}). "
                f"Use strategy='truncate_prompt' to allow left-truncation."
            )
        # Left-truncate prompt to context_length - 1 to allow at least 1 new token
        allowed_prompt_len = max(1, context_length - min(max_new_tokens, context_length - 1))
        prompt_ids = prompt_ids[-allowed_prompt_len:]
        prompt_len = len(prompt_ids)

    if prompt_len + max_new_tokens > context_length:
        if strategy == "error":
            raise ContextOverflowError(
                f"Prompt length ({prompt_len}) + max_new_tokens ({max_new_tokens}) = "
                f"{prompt_len + max_new_tokens}, exceeding model context length ({context_length})."
            )
        elif strategy == "truncate_prompt":
            # Determine maximum prompt tokens we can keep
            max_allowed_prompt = context_length - max_new_tokens
            if max_allowed_prompt >= 1:
                # Truncate oldest prompt tokens from the left
                prompt_ids = prompt_ids[-max_allowed_prompt:]
            else:
                # If max_new_tokens alone takes almost all context, keep 1 prompt token and clamp new tokens
                prompt_ids = prompt_ids[-1:]
                max_new_tokens = context_length - 1
        else:
            raise ValueError(f"Unsupported context overflow strategy: '{strategy}'")

    effective_max_new = min(max_new_tokens, context_length - len(prompt_ids))
    return prompt_ids, effective_max_new
