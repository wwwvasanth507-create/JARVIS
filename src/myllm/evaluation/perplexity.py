"""
Validation Perplexity and Token-Weighted Loss Calculation.

Evaluates trained models using exact token-weighted cross-entropy aggregation,
guaranteeing CPU safety, torch.no_grad(), and model.eval().
"""

from __future__ import annotations

import logging
import time
from typing import Optional
import torch
import torch.nn as nn
from myllm.data.batching import BatchGenerator
from myllm.data.dataset import TokenDataset
from myllm.evaluation.metrics import EvaluationMetrics, calculate_perplexity

logger = logging.getLogger(__name__)


def evaluate_perplexity(
    model: nn.Module,
    dataset: TokenDataset,
    batch_size: int = 4,
    eval_batches: Optional[int] = None,
    seed: Optional[int] = 42,
) -> EvaluationMetrics:
    """
    Compute token-weighted cross-entropy loss and perplexity on CPU.

    Args:
        model: PyTorch model to evaluate.
        dataset: Validation TokenDataset.
        batch_size: Batch size for evaluation.
        eval_batches: Optional maximum number of batches to evaluate (evaluates all if None).
        seed: Random seed for deterministic batch creation.

    Returns:
        EvaluationMetrics with token-weighted mean loss, perplexity, and throughput.
    """
    if len(dataset) == 0:
        return EvaluationMetrics(
            total_tokens=0,
            num_batches=0,
            mean_loss=float("nan"),
            perplexity=float("nan"),
            elapsed_time_sec=0.0,
            tokens_per_sec=0.0,
        )

    was_training = model.training
    model.eval()

    val_gen = BatchGenerator(
        dataset=dataset,
        batch_size=batch_size,
        shuffle=False,
        seed=seed,
        drop_last=False,
    )

    total_weighted_loss = 0.0
    total_tokens = 0
    num_batches = 0
    start_time = time.perf_counter()

    try:
        with torch.no_grad():
            for step, (input_ids, labels) in enumerate(val_gen):
                if eval_batches is not None and step >= eval_batches:
                    break

                # Labels are shifted in GPTModel: target tokens are labels[:, 1:]
                shift_labels = labels[:, 1:].contiguous()
                valid_mask = shift_labels != -100
                batch_tokens = int(valid_mask.sum().item())

                if batch_tokens == 0:
                    continue

                _, loss = model(input_ids, labels=labels)
                batch_loss = float(loss.item())

                # Token-weighted aggregation
                total_weighted_loss += batch_loss * batch_tokens
                total_tokens += batch_tokens
                num_batches += 1

    finally:
        model.train(was_training)

    elapsed = time.perf_counter() - start_time
    if total_tokens == 0 or num_batches == 0:
        mean_loss = float("nan")
        ppl = float("nan")
        tps = 0.0
    else:
        mean_loss = total_weighted_loss / total_tokens
        ppl = calculate_perplexity(mean_loss)
        tps = total_tokens / elapsed if elapsed > 0 else 0.0

    return EvaluationMetrics(
        total_tokens=total_tokens,
        num_batches=num_batches,
        mean_loss=mean_loss,
        perplexity=ppl,
        elapsed_time_sec=elapsed,
        tokens_per_sec=tps,
    )
