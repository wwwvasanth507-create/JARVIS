"""
Model inspection and parameter counting utilities for MyLLM.

Provides accurate parameter counting (accounting for shared/tied weights)
and structured architecture summaries.
"""

from __future__ import annotations

from typing import Any, Dict, Set
import torch
import torch.nn as nn


def count_parameters(model: nn.Module) -> Dict[str, int]:
    """
    Count total, trainable, and non-trainable parameters in a model.

    Correctly handles tied/shared weights so that shared tensors are counted only once.

    Args:
        model: PyTorch nn.Module instance.

    Returns:
        Dictionary with 'total', 'trainable', and 'non_trainable' parameter counts.
    """
    seen_params: Set[int] = set()
    total_params = 0
    trainable_params = 0

    for param in model.parameters():
        param_id = id(param)
        if param_id in seen_params:
            continue
        seen_params.add(param_id)

        numel = param.numel()
        total_params += numel
        if param.requires_grad:
            trainable_params += numel

    non_trainable_params = total_params - trainable_params

    return {
        "total": total_params,
        "trainable": trainable_params,
        "non_trainable": non_trainable_params,
    }


def get_model_summary(model: nn.Module) -> str:
    """
    Generate a human-readable architectural and parameter summary of the model.

    Args:
        model: PyTorch nn.Module instance.

    Returns:
        Formatted multi-line summary string.
    """
    counts = count_parameters(model)
    total_m = counts["total"] / 1e6
    mem_mb = (counts["total"] * 4) / (1024 * 1024)  # 4 bytes per float32 param

    lines = [
        "=" * 60,
        f"                 Model Summary: {model.__class__.__name__}                 ",
        "=" * 60,
        f"Total Parameters         : {counts['total']:,} ({total_m:.3f}M)",
        f"Trainable Parameters     : {counts['trainable']:,}",
        f"Non-Trainable Parameters : {counts['non_trainable']:,}",
        f"Estimated Parameter Size : {mem_mb:.2f} MB (float32)",
        "-" * 60,
    ]

    # Sub-component breakdown if model has expected GPT structure
    if hasattr(model, "transformer"):
        t = model.transformer
        if hasattr(t, "wte"):
            lines.append(f"Token Embedding (wte)    : {t.wte.weight.numel():,} params ({t.wte.weight.shape})")
        if hasattr(t, "wpe"):
            lines.append(f"Position Embedding (wpe) : {t.wpe.weight.numel():,} params ({t.wpe.weight.shape})")
        if hasattr(t, "h"):
            n_blocks = len(t.h)
            block_params = sum(p.numel() for p in t.h[0].parameters())
            lines.append(f"Transformer Blocks ({n_blocks}x)  : {block_params * n_blocks:,} params ({block_params:,} per block)")
        if hasattr(t, "ln_f"):
            ln_params = sum(p.numel() for p in t.ln_f.parameters())
            lines.append(f"Final LayerNorm (ln_f)   : {ln_params:,} params")
    if hasattr(model, "lm_head"):
        is_tied = hasattr(model, "transformer") and hasattr(model.transformer, "wte") and (model.lm_head.weight is model.transformer.wte.weight)
        status = "Tied with wte" if is_tied else f"{model.lm_head.weight.numel():,} params"
        lines.append(f"LM Head                  : {status} ({model.lm_head.weight.shape})")

    lines.append("=" * 60)
    return "\n".join(lines)
