"""
Complete GPT-Style Decoder-Only Transformer Language Model for MyLLM.

Pre-LayerNorm architecture with learned positional embeddings,
causal multi-head self-attention, GELU MLP, and optional weight tying.
Strictly CPU-first.
"""

from __future__ import annotations

import math
from typing import Optional, Tuple, Union
import torch
import torch.nn as nn
from torch.nn import functional as F
from myllm.config import ModelConfig
from myllm.model.block import TransformerBlock


class GPTModel(nn.Module):
    """
    GPT-Style Decoder-Only Transformer Language Model.

    Forward Pipeline:
        Token IDs [B, T]
           ↓
        Token Embedding [B, T, C] + Learned Positional Embedding [1, T, C]
           ↓
        Dropout
           ↓
        Transformer Blocks × n_layer [Pre-LN Causal Attention + Pre-LN MLP]
           ↓
        Final LayerNorm [B, T, C]
           ↓
        LM Head [B, T, vocab_size] (Optionally weight-tied with Token Embedding)
           ↓
        Vocabulary Logits [B, T, vocab_size] (and optional Cross-Entropy Loss)
    """

    def __init__(self, config: ModelConfig) -> None:
        super().__init__()
        self.config = config

        self.transformer = nn.ModuleDict(
            dict(
                wte=nn.Embedding(config.vocab_size, config.n_embd),
                wpe=nn.Embedding(config.context_length, config.n_embd),
                drop=nn.Dropout(config.dropout),
                h=nn.ModuleList([TransformerBlock(config) for _ in range(config.n_layer)]),
                ln_f=nn.LayerNorm(config.n_embd),
            )
        )

        self.lm_head = nn.Linear(config.n_embd, config.vocab_size, bias=False)

        # Weight tying: share weights between input token embedding and output projection
        if config.weight_tying:
            self.lm_head.weight = self.transformer.wte.weight

        # Initialize all model weights using GPT-2 principles
        self.apply(self._init_weights)

        # Apply residual projection scaling: scale residual projections by 1 / sqrt(2 * n_layer)
        for pn, p in self.named_parameters():
            if pn.endswith("c_proj.weight"):
                torch.nn.init.normal_(
                    p,
                    mean=0.0,
                    std=0.02 / math.sqrt(2 * config.n_layer),
                )

    def _init_weights(self, module: nn.Module) -> None:
        """
        Initialize module parameters with standard Gaussian distribution.

        - Linear weights: Normal(0, 0.02)
        - Linear biases: Zeros
        - Embedding weights: Normal(0, 0.02)
        - LayerNorm weights: Ones, biases: Zeros
        """
        if isinstance(module, nn.Linear):
            torch.nn.init.normal_(module.weight, mean=0.0, std=0.02)
            if module.bias is not None:
                torch.nn.init.zeros_(module.bias)
        elif isinstance(module, nn.Embedding):
            torch.nn.init.normal_(module.weight, mean=0.0, std=0.02)
        elif isinstance(module, nn.LayerNorm):
            torch.nn.init.zeros_(module.bias)
            torch.nn.init.ones_(module.weight)

    def forward(
        self,
        input_ids: torch.Tensor,
        labels: Optional[torch.Tensor] = None,
    ) -> Union[torch.Tensor, Tuple[torch.Tensor, torch.Tensor]]:
        """
        Forward pass of the language model.

        Args:
            input_ids: Integer tensor of shape [B, T] with token IDs in [0, vocab_size).
            labels: Optional target token IDs of shape [B, T] for next-token prediction loss.

        Returns:
            If labels is None:
                logits of shape [B, T, vocab_size]
            If labels is provided:
                tuple of (logits, loss) where loss is a scalar torch.Tensor.

        Raises:
            ValueError: If input sequence length T > context_length, or if token IDs are out of bounds.
        """
        if input_ids.dim() != 2:
            raise ValueError(f"input_ids must be 2D tensor [B, T], got shape {list(input_ids.shape)}.")

        B, T = input_ids.size()

        if T > self.config.context_length:
            raise ValueError(
                f"Sequence length T={T} exceeds maximum context length {self.config.context_length}."
            )

        # Token ID validation
        if (input_ids < 0).any() or (input_ids >= self.config.vocab_size).any():
            min_val = int(input_ids.min().item())
            max_val = int(input_ids.max().item())
            raise ValueError(
                f"Token IDs out of vocabulary bounds [0, {self.config.vocab_size - 1}]. "
                f"Found values in range [{min_val}, {max_val}]."
            )

        # Position indices: [T]
        pos = torch.arange(0, T, dtype=torch.long, device=input_ids.device)

        # 1. Embeddings: token + learned position
        tok_emb = self.transformer.wte(input_ids)  # [B, T, C]
        pos_emb = self.transformer.wpe(pos)        # [T, C]
        x = self.transformer.drop(tok_emb + pos_emb)

        # 2. Sequential Transformer Blocks
        for block in self.transformer.h:
            x = block(x)

        # 3. Final LayerNorm
        x = self.transformer.ln_f(x)

        # 4. Language Model Head -> Logits
        logits = self.lm_head(x)  # [B, T, vocab_size]

        # 5. Optional loss calculation using next-token prediction
        if labels is not None:
            if labels.dim() != 2 or labels.size() != input_ids.size():
                raise ValueError(
                    f"labels shape {list(labels.shape)} must match input_ids shape {list(input_ids.shape)}."
                )

            # Shift so that tokens < n predict n
            shift_logits = logits[:, :-1, :].contiguous()
            shift_labels = labels[:, 1:].contiguous()

            # Flatten batch and sequence dimensions for cross-entropy loss
            loss = F.cross_entropy(
                shift_logits.view(-1, shift_logits.size(-1)),
                shift_labels.view(-1),
                ignore_index=-100,
            )
            return logits, loss

        return logits
