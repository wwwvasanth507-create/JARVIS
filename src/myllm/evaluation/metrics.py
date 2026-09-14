"""
Evaluation metrics structures for MyLLM.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Any, Dict


def calculate_perplexity(loss: float) -> float:
    """
    Calculate perplexity from cross-entropy loss: PPL = exp(loss).

    Guards against overflow by capping exponent at 100.0 (returns inf if loss > 100).
    Returns NaN if loss is NaN.
    """
    if math.isnan(loss):
        return float("nan")
    if loss > 100.0:
        return float("inf")
    try:
        return math.exp(loss)
    except OverflowError:
        return float("inf")


@dataclass
class EvaluationMetrics:
    """Structured metrics returned from perplexity evaluation."""
    total_tokens: int
    num_batches: int
    mean_loss: float
    perplexity: float
    elapsed_time_sec: float
    tokens_per_sec: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
