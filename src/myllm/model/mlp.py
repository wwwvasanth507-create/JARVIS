"""
Feed-Forward Network (MLP) module for MyLLM Transformer.

Standard GPT 4x expansion with configurable activation (GELU) and dropout.
"""

from __future__ import annotations

import torch
import torch.nn as nn
from myllm.config import ModelConfig


def get_activation_fn(activation_name: str) -> nn.Module:
    """Return activation module by string name."""
    name = activation_name.lower().strip()
    if name == "gelu":
        return nn.GELU()
    elif name == "gelu_tanh":
        return nn.GELU(approximate="tanh")
    elif name == "relu":
        return nn.ReLU()
    elif name == "silu":
        return nn.SiLU()
    elif name == "tanh":
        return nn.Tanh()
    else:
        raise ValueError(f"Unsupported activation function: '{activation_name}'")


class MLP(nn.Module):
    """
    Position-wise Feed-Forward Network.

    Architecture:
        Linear(C, 4 * C) -> Activation -> Linear(4 * C, C) -> Dropout
    """

    def __init__(self, config: ModelConfig) -> None:
        super().__init__()
        self.c_fc = nn.Linear(config.n_embd, 4 * config.n_embd, bias=config.bias)
        self.act = get_activation_fn(config.activation)
        self.c_proj = nn.Linear(4 * config.n_embd, config.n_embd, bias=config.bias)
        self.dropout = nn.Dropout(config.dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass for Feed-Forward Network.

        Args:
            x: Input tensor of shape [B, T, C].

        Returns:
            Output tensor of shape [B, T, C].
        """
        # [B, T, C] -> [B, T, 4 * C]
        h = self.c_fc(x)
        h = self.act(h)
        # [B, T, 4 * C] -> [B, T, C]
        h = self.c_proj(h)
        h = self.dropout(h)
        return h
