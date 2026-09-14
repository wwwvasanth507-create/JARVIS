"""
Multi-Head Causal Self-Attention module for MyLLM.

Implements scaled dot-product attention with strict lower-triangular causal masking
and fused QKV projection for CPU-first execution.
"""

from __future__ import annotations

import math
from typing import Optional, Tuple, Union
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

    def forward(
        self,
        x: torch.Tensor,
        past_key_value: Optional[Tuple[torch.Tensor, torch.Tensor]] = None,
        use_cache: bool = False,
    ) -> Union[torch.Tensor, Tuple[torch.Tensor, Tuple[torch.Tensor, torch.Tensor]]]:
        """
        Forward pass for Causal Self-Attention.

        Args:
            x: Input tensor of shape [B, T, C].
            past_key_value: Optional cached (K, V) tuple from previous steps.
                            Each of shape [B, n_head, past_len, head_dim].
            use_cache: If True, returns (output, (present_k, present_v)).

        Returns:
            Output tensor of shape [B, T, C] if use_cache is False,
            otherwise tuple of (output, (present_k, present_v)).
        """
        B, T, C = x.size()

        # 1. Project Q, K, V in a single matrix multiplication
        # [B, T, C] -> [B, T, 3 * C]
        qkv = self.c_attn(x)

        # Split into q, k, v each of shape [B, T, C]
        q, k, v = qkv.split(self.n_embd, dim=2)

        # 2. Reshape into multi-head format: [B, T, C] -> [B, n_head, T, head_dim]
        q = q.view(B, T, self.n_head, self.head_dim).transpose(1, 2)
        k = k.view(B, T, self.n_head, self.head_dim).transpose(1, 2)
        v = v.view(B, T, self.n_head, self.head_dim).transpose(1, 2)

        # 3. Concatenate past cached keys and values if available
        if past_key_value is not None:
            past_k, past_v = past_key_value
            k = torch.cat([past_k, k], dim=2)
            v = torch.cat([past_v, v], dim=2)

        present_key_value = (k, v) if use_cache else None
        total_len = k.size(2)

        if total_len > self.context_length:
            raise ValueError(
                f"Total sequence length {total_len} exceeds maximum context length {self.context_length}."
            )

        dropout_p = self.attn_dropout.p if self.training else 0.0

        # 4-7. Efficient scaled dot-product attention
        if past_key_value is None:
            # Full sequence forward pass (training or prefill): causal mask ensures j <= i
            y = F.scaled_dot_product_attention(
                q, k, v,
                attn_mask=None,
                dropout_p=dropout_p,
                is_causal=True,
            )
        elif T == 1:
            # Single-token incremental decode with past cache:
            # Current query attends to all past and present keys without causal restriction
            y = F.scaled_dot_product_attention(
                q, k, v,
                attn_mask=None,
                dropout_p=dropout_p,
                is_causal=False,
            )
        else:
            # Multi-token continuation with past cache:
            # Query positions [past_len .. total_len-1] attend to key positions <= query position
            past_len = past_key_value[0].size(2)
            q_pos = torch.arange(past_len, total_len, device=x.device).unsqueeze(1)
            k_pos = torch.arange(0, total_len, device=x.device).unsqueeze(0)
            mask = (k_pos <= q_pos).view(1, 1, T, total_len)
            y = F.scaled_dot_product_attention(
                q, k, v,
                attn_mask=mask,
                dropout_p=dropout_p,
                is_causal=False,
            )

        # 8. Recombine heads:
        # [B, n_head, T, head_dim] -> [B, T, n_head, head_dim] -> [B, T, C]
        y = y.transpose(1, 2).contiguous().view(B, T, C)

        # 9. Output projection with residual dropout
        # [B, T, C] -> [B, T, C]
        y = self.resid_dropout(self.c_proj(y))

        if use_cache:
            return y, present_key_value
        return y

