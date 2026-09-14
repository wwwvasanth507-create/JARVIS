"""
Transformer Decoder Block for MyLLM.

Implements Pre-LayerNorm architecture with Causal Self-Attention,
Feed-Forward Network, and residual connections.
"""

from __future__ import annotations

from typing import Optional, Tuple, Union
import torch
import torch.nn as nn
from myllm.config import ModelConfig
from myllm.model.attention import CausalSelfAttention
from myllm.model.mlp import MLP


class TransformerBlock(nn.Module):
    """
    Pre-LayerNorm Transformer Decoder Block.

    Dataflow:
        x = x + Attention(ln_1(x))
        x = x + MLP(ln_2(x))
    """

    def __init__(self, config: ModelConfig) -> None:
        super().__init__()
        self.ln_1 = nn.LayerNorm(config.n_embd)
        self.attn = CausalSelfAttention(config)
        self.ln_2 = nn.LayerNorm(config.n_embd)
        self.mlp = MLP(config)

    def forward(
        self,
        x: torch.Tensor,
        past_key_value: Optional[Tuple[torch.Tensor, torch.Tensor]] = None,
        use_cache: bool = False,
    ) -> Union[torch.Tensor, Tuple[torch.Tensor, Tuple[torch.Tensor, torch.Tensor]]]:
        """
        Forward pass for TransformerBlock.

        Args:
            x: Input tensor of shape [B, T, C].
            past_key_value: Optional cached (K, V) tuple from previous steps.
            use_cache: If True, returns (output, (present_k, present_v)).

        Returns:
            Output tensor of shape [B, T, C] if use_cache is False,
            otherwise tuple of (output, present_key_value).
        """
        # Pre-LN Self-Attention with residual connection
        if use_cache:
            attn_out, present_key_value = self.attn(
                self.ln_1(x), past_key_value=past_key_value, use_cache=True
            )
        else:
            attn_out = self.attn(self.ln_1(x), past_key_value=past_key_value, use_cache=False)
            present_key_value = None

        x = x + attn_out

        # Pre-LN MLP with residual connection
        x = x + self.mlp(self.ln_2(x))

        if use_cache:
            return x, present_key_value
        return x

