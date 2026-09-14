"""
Optimizer configuration and parameter group partitioning for MyLLM.

Implements AdamW optimization with decoupled weight decay:
- 2D parameters (Linear weights, Embedding tables) receive weight decay.
- 1D parameters (biases, LayerNorm scales and biases) receive 0.0 weight decay.
Guarantees parameter uniqueness and handles weight tying safely.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Tuple
import torch
import torch.nn as nn
from myllm.config import TrainingConfig

logger = logging.getLogger(__name__)


def partition_parameters(model: nn.Module) -> Tuple[List[nn.Parameter], List[nn.Parameter]]:
    """
    Partition model parameters into weight-decay and non-weight-decay groups.

    Rules:
    - 2D or higher-dimensional tensors (e.g. Linear weights, Embedding weights) -> weight decay.
    - 1D tensors (e.g. Biases, LayerNorm scale/bias) -> no weight decay.
    - Preserves parameter uniqueness when weights are tied (e.g., wte / lm_head).

    Args:
        model: PyTorch module.

    Returns:
        Tuple of (decay_params, no_decay_params).
    """
    decay_params: List[nn.Parameter] = []
    no_decay_params: List[nn.Parameter] = []
    seen_param_ids = set()

    for name, param in model.named_parameters():
        if not param.requires_grad:
            continue
        if id(param) in seen_param_ids:
            continue
        seen_param_ids.add(id(param))

        # Biases and 1D normalization parameters receive zero weight decay
        if param.dim() < 2 or name.endswith(".bias"):
            no_decay_params.append(param)
        else:
            decay_params.append(param)

    return decay_params, no_decay_params


def create_optimizer(model: nn.Module, config: TrainingConfig) -> torch.optim.AdamW:
    """
    Construct an AdamW optimizer for the model according to TrainingConfig.

    Args:
        model: PyTorch neural network module on CPU.
        config: Training configuration with learning rate, betas, eps, and weight decay.

    Returns:
        Configured torch.optim.AdamW optimizer.
    """
    decay_params, no_decay_params = partition_parameters(model)

    num_decay = sum(p.numel() for p in decay_params)
    num_no_decay = sum(p.numel() for p in no_decay_params)

    logger.debug(
        f"Optimizer parameter groups: "
        f"{len(decay_params)} decayed tensors ({num_decay:,} params), "
        f"{len(no_decay_params)} non-decayed tensors ({num_no_decay:,} params)."
    )

    param_groups = [
        {"params": decay_params, "weight_decay": config.weight_decay},
        {"params": no_decay_params, "weight_decay": 0.0},
    ]

    optimizer = torch.optim.AdamW(
        param_groups,
        lr=config.learning_rate,
        betas=(config.beta1, config.beta2),
        eps=config.eps,
    )
    return optimizer
