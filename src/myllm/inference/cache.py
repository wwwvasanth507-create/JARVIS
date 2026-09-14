"""
Key-Value (KV) Cache Management for MyLLM.

Manages cached key and value tensors per layer to avoid recomputing
past positions during autoregressive generation on CPU.
"""

from __future__ import annotations

from typing import List, Optional, Tuple
import torch


class KVCache:
    """
    Manages key and value states across Transformer decoder layers.

    Shape for each layer:
        Key:   [B, n_head, sequence_length, head_dim]
        Value: [B, n_head, sequence_length, head_dim]
    """

    def __init__(self, context_length: int) -> None:
        self.context_length = context_length
        self._past_key_values: Optional[List[Tuple[torch.Tensor, torch.Tensor]]] = None

    def reset(self) -> None:
        """Clear all cached keys and values."""
        self._past_key_values = None

    @property
    def is_empty(self) -> bool:
        """Return True if cache contains no past tokens."""
        return self._past_key_values is None or len(self._past_key_values) == 0

    @property
    def current_length(self) -> int:
        """Return the number of cached token positions."""
        if self.is_empty or self._past_key_values[0] is None:
            return 0
        return self._past_key_values[0][0].size(2)

    @property
    def past_key_values(self) -> Optional[List[Tuple[torch.Tensor, torch.Tensor]]]:
        """Get the cached key-values list for model forward pass."""
        return self._past_key_values

    def update(self, present_key_values: List[Tuple[torch.Tensor, torch.Tensor]]) -> None:
        """
        Update cached keys and values with output from latest forward pass.

        Args:
            present_key_values: List of (K, V) tuples from each layer.
        """
        self._past_key_values = present_key_values
        new_len = self.current_length
        if new_len > self.context_length:
            raise ValueError(
                f"KV cache length ({new_len}) exceeds maximum context length ({self.context_length})."
            )

    def get_shape(self) -> Optional[Tuple[int, int, int, int]]:
        """Return (batch_size, n_head, seq_len, head_dim) of cached tensors, if present."""
        if self.is_empty:
            return None
        k = self._past_key_values[0][0]
        return tuple(k.shape)  # type: ignore
