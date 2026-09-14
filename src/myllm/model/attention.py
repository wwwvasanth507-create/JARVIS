"""
Multi-Head Causal Self-Attention module for MyLLM.

Implements scaled dot-product attention with strict lower-triangular causal masking
and fused QKV projection for CPU-first execution.
"""

from __future__ import annotations

import math
import torch
import torch.nn as nn
from torch.nn import functional as F
from myllm.config import ModelConfig


class CausalSelfAttention(nn.Module):
    """
    Multi-Head Causal Self-Attention.

    Projects input embeddings into Query, Key, and Value representations,
    computes scaled dot-product attention scores, applies causal masking so tokens
    cannot attend to future positions, and projects the combined head outputs.

    Expected tensor shapes:
        Input:            [B, T, C] where C = n_embd
        Q, K, V:          [B, n_head, T, head_dim] where head_dim = C // n_head
        Attention scores: [B, n_head, T, T]
        Attention output: [B, n_head, T, head_dim]
        Merged:           [B, T, C]
        Final Output:     [B, T, C]
    """

    def __init__(self, config: ModelConfig) -> None:
        super().__init__()
        self.n_head = config.n_head
        self.n_embd = config.n_embd
        self.head_dim = config.head_dim
        self.context_length = config.context_length

        # Fused Q, K, V projection: [B, T, C] -> [B, T, 3 * C]
        self.c_attn = nn.Linear(self.n_embd, 3 * self.n_embd, bias=config.bias)

        # Output projection: [B, T, C] -> [B, T, C]
        self.c_proj = nn.Linear(self.n_embd, self.n_embd, bias=config.bias)

        # Regularization dropouts
        self.attn_dropout = nn.Dropout(config.dropout)
        self.resid_dropout = nn.Dropout(config.dropout)

        # Causal mask: lower-triangular matrix of 1s (diagonal and lower allowed, upper blocked)
        # Registered as non-trainable buffer moving with module device
        mask = torch.tril(torch.ones(self.context_length, self.context_length))
        self.register_buffer(
            "causal_mask",
            mask.view(1, 1, self.context_length, self.context_length),
            persistent=False,
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass for Causal Self-Attention.

        Args:
            x: Input tensor of shape [B, T, C].

        Returns:
            Output tensor of shape [B, T, C].
        """
        B, T, C = x.size()

        if T > self.context_length:
            raise ValueError(
                f"Sequence length T={T} exceeds maximum context length {self.context_length}."
            )

        # 1. Project Q, K, V in a single matrix multiplication
        # [B, T, C] -> [B, T, 3 * C]
        qkv = self.c_attn(x)

        # Split into q, k, v each of shape [B, T, C]
        q, k, v = qkv.split(self.n_embd, dim=2)

        # 2. Reshape into multi-head format: [B, T, C] -> [B, n_head, T, head_dim]
        q = q.view(B, T, self.n_head, self.head_dim).transpose(1, 2)
        k = k.view(B, T, self.n_head, self.head_dim).transpose(1, 2)
        v = v.view(B, T, self.n_head, self.head_dim).transpose(1, 2)

        # 3. Scaled dot-product attention scores:
        # [B, n_head, T, head_dim] @ [B, n_head, head_dim, T] -> [B, n_head, T, T]
        scale = 1.0 / math.sqrt(self.head_dim)
        att = (q @ k.transpose(-2, -1)) * scale

        # 4. Apply strict causal masking:
        # Future positions j > i are set to -inf so softmax gives zero probability
        att = att.masked_fill(self.causal_mask[:, :, :T, :T] == 0, float("-inf"))

        # 5. Softmax over target sequence dimension T
        # [B, n_head, T, T]
        att = F.softmax(att, dim=-1)
        att = self.attn_dropout(att)

        # 6. Values aggregation:
        # [B, n_head, T, T] @ [B, n_head, T, head_dim] -> [B, n_head, T, head_dim]
        y = att @ v

        # 7. Recombine heads:
        # [B, n_head, T, head_dim] -> [B, T, n_head, head_dim] -> [B, T, C]
        y = y.transpose(1, 2).contiguous().view(B, T, C)

        # 8. Output projection with residual dropout
        # [B, T, C] -> [B, T, C]
        y = self.resid_dropout(self.c_proj(y))

        return y
