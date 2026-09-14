"""
Deterministic Validation Loop for MyLLM.

Computes validation loss and perplexity on CPU using torch.no_grad() and model.eval().
Guarantees restoration of previous model training mode and leaves optimizer untouched.
"""

from __future__ import annotations

import logging
from typing import Optional, Tuple
import torch
import torch.nn as nn
from myllm.data.batching import BatchGenerator
from myllm.data.dataset import TokenDataset
from myllm.training.metrics import calculate_perplexity

logger = logging.getLogger(__name__)


def evaluate(
    model: nn.Module,
    val_dataset: TokenDataset,
    batch_size: int = 4,
    eval_batches: int = 10,
    seed: Optional[int] = 42,
) -> Tuple[float, float]:
    """
    Run evaluation loop without gradients over validation dataset.

    Args:
        model: PyTorch model.
        val_dataset: Validation TokenDataset.
        batch_size: Batch size for validation.
        eval_batches: Maximum number of batches to evaluate.
        seed: Random seed for deterministic validation batch sampling.

    Returns:
        Tuple of (average_validation_loss, validation_perplexity).
    """
    if len(val_dataset) == 0:
        return float("nan"), float("nan")

    # Record previous training state
    was_training = model.training
    model.eval()

    total_loss = 0.0
    num_batches = 0

    val_gen = BatchGenerator(
        dataset=val_dataset,
        batch_size=batch_size,
        shuffle=False,
        seed=seed,
        drop_last=False,
    )

    try:
        with torch.no_grad():
            for step, (input_ids, labels) in enumerate(val_gen):
                if step >= eval_batches:
                    break
                _, loss = model(input_ids, labels=labels)
                total_loss += float(loss.item())
                num_batches += 1
    finally:
        # Guarantee restoring previous model mode
        model.train(was_training)

    if num_batches == 0:
        return float("nan"), float("nan")

    avg_loss = total_loss / num_batches
    perplexity = calculate_perplexity(avg_loss)
    return avg_loss, perplexity
