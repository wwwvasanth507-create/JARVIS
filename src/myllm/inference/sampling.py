"""
Sampling and logit manipulation for MyLLM inference.

Strictly follows the documented pipeline:
raw logits -> repetition penalty -> temperature -> top-k -> top-p -> softmax -> sample/argmax.
"""

from __future__ import annotations

from typing import Optional, Sequence
import torch
import torch.nn.functional as F
from myllm.inference.types import GenerationConfig


class InferenceError(RuntimeError):
    """Raised when an inference or sampling failure occurs (e.g. non-finite logits)."""


def apply_repetition_penalty(
    logits: torch.Tensor,
    seen_tokens: Sequence[int],
    penalty: float,
) -> torch.Tensor:
    """
    Apply repetition penalty to logits of previously generated or prompt tokens.

    Rules:
    - If logit > 0: logit /= penalty
    - If logit <= 0: logit *= penalty
    - If penalty == 1.0: no-op

    Args:
        logits: 1D tensor [vocab_size].
        seen_tokens: Sequence of integer token IDs.
        penalty: Repetition penalty coefficient (> 0).

    Returns:
        Modified logits tensor.
    """
    if penalty == 1.0 or not seen_tokens:
        return logits

    logits = logits.clone()
    unique_tokens = set(seen_tokens)
    vocab_size = logits.size(-1)

    for tok in unique_tokens:
        if 0 <= tok < vocab_size:
            val = logits[tok].item()
            if val > 0:
                logits[tok] = val / penalty
            else:
                logits[tok] = val * penalty

    return logits


def apply_temperature(logits: torch.Tensor, temperature: float) -> torch.Tensor:
    """
    Scale logits by temperature factor.

    Args:
        logits: 1D tensor [vocab_size].
        temperature: Temperature value (> 0).

    Returns:
        Scaled logits tensor.
    """
    if temperature == 1.0:
        return logits
    return logits / temperature


def apply_top_k(logits: torch.Tensor, top_k: int) -> torch.Tensor:
    """
    Filter logits keeping only the top-K highest values (setting others to -inf).

    Args:
        logits: 1D tensor [vocab_size].
        top_k: Number of highest logits to preserve (0 disables).

    Returns:
        Filtered logits tensor.
    """
    if top_k <= 0:
        return logits

    vocab_size = logits.size(-1)
    k = min(top_k, vocab_size)

    # Top-K values
    top_values, _ = torch.topk(logits, k)
    min_allowed = top_values[-1]
    return torch.where(logits < min_allowed, torch.tensor(float("-inf"), device=logits.device), logits)


def apply_top_p(logits: torch.Tensor, top_p: float) -> torch.Tensor:
    """
    Nucleus (top-p) filtering: preserves tokens comprising the top-p cumulative probability mass.

    Args:
        logits: 1D tensor [vocab_size].
        top_p: Probability mass threshold in (0.0, 1.0] (1.0 disables).

    Returns:
        Filtered logits tensor.
    """
    if top_p >= 1.0:
        return logits

    # Sort logits in descending order
    sorted_logits, sorted_indices = torch.sort(logits, descending=True)
    probs = F.softmax(sorted_logits, dim=-1)
    cumulative_probs = torch.cumsum(probs, dim=-1)

    # Remove tokens with cumulative probability > top_p, but always keep the first token
    sorted_indices_to_remove = cumulative_probs > top_p
    # Shift right so the first token exceeding threshold is preserved
    sorted_indices_to_remove[1:] = sorted_indices_to_remove[:-1].clone()
    sorted_indices_to_remove[0] = False

    # Scatter back to original indices
    indices_to_remove = sorted_indices[sorted_indices_to_remove]
    filtered_logits = logits.clone()
    filtered_logits[indices_to_remove] = float("-inf")
    return filtered_logits


def sample_next_token(
    logits: torch.Tensor,
    seen_tokens: Sequence[int],
    config: GenerationConfig,
    generator: Optional[torch.Generator] = None,
) -> int:
    """
    Sample the next token ID from raw model logits following the exact pipeline:
    raw logits -> repetition penalty -> temperature -> top-k -> top-p -> softmax -> sample/argmax.

    Args:
        logits: 1D or 2D tensor of logits for the final sequence position [vocab_size].
        seen_tokens: Token IDs generated so far for repetition penalization.
        config: GenerationConfig defining sampling parameters.
        generator: Optional PyTorch CPU Generator for seeded reproducibility.

    Returns:
        Sampled integer token ID.

    Raises:
        InferenceError: If logits contain NaN or Inf values.
    """
    if logits.dim() > 1:
        logits = logits.squeeze()
    if logits.dim() != 1:
        raise ValueError(f"Expected 1D logits tensor, got shape {list(logits.shape)}")

    # 1. Validate logit finiteness
    if not torch.isfinite(logits).all():
        raise InferenceError("Encountered non-finite values (NaN or Inf) in model logits.")

    # 2. Greedy decoding shortcut
    if not config.do_sample:
        # Repetition penalty still applies if configured
        if config.repetition_penalty != 1.0 and seen_tokens:
            logits = apply_repetition_penalty(logits, seen_tokens, config.repetition_penalty)
        return int(torch.argmax(logits).item())

    # 3. Repetition penalty
    if config.repetition_penalty != 1.0 and seen_tokens:
        logits = apply_repetition_penalty(logits, seen_tokens, config.repetition_penalty)

    # 4. Temperature scaling
    logits = apply_temperature(logits, config.temperature)

    # 5. Top-K filtering
    logits = apply_top_k(logits, config.top_k)

    # 6. Top-P (nucleus) filtering
    logits = apply_top_p(logits, config.top_p)

    # Fallback safety: if all tokens were masked to -inf, fall back to argmax
    if torch.isinf(logits).all():
        return int(torch.argmax(logits).item())

    # 7. Softmax to probability distribution
    probs = F.softmax(logits, dim=-1)

    # 8. Sample next token
    token = torch.multinomial(probs, num_samples=1, generator=generator)
    return int(token.item())
