"""
Transformer Decoder Block for MyLLM.

Implements Pre-LayerNorm architecture with Causal Self-Attention,
Feed-Forward Network, and residual connections.
"""

from __future__ import annotations

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

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass for TransformerBlock.

        Args:
            x: Input tensor of shape [B, T, C].

        Returns:
            Output tensor of shape [B, T, C].
        """
        # Pre-LN Self-Attention with residual connection
        x = x + self.attn(self.ln_1(x))

        # Pre-LN MLP with residual connection
        x = x + self.mlp(self.ln_2(x))

        return x
