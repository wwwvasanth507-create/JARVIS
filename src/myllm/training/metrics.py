"""
Metrics and throughput tracking for MyLLM training engine.

Calculates cross-entropy perplexity with numerical overflow protection,
tracks CPU training throughput (tokens/sec, steps/sec), and formats structured logs.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import math
import time
from typing import Any, Dict, Optional


def calculate_perplexity(loss: float) -> float:
    """
    Compute language model perplexity from cross-entropy loss: ppl = exp(loss).

    Guarantees:
    - Rejects negative loss values with ValueError.
    - Gracefully handles numerical overflow (e.g., loss > 85.0) by returning float('inf') instead of crashing or NaN.
    - Returns float('inf') if loss is NaN or infinite.

    Args:
        loss: Scalar cross-entropy loss value.

    Returns:
        Perplexity as float, or float('inf') upon overflow.
    """
    if math.isnan(loss) or math.isinf(loss):
        return float("inf")
    if loss < 0.0:
        raise ValueError(f"Cross-entropy loss cannot be negative, got {loss}")
    if loss > 85.0:
        return float("inf")
    try:
        return math.exp(loss)
    except OverflowError:
        return float("inf")


@dataclass
class StepMetrics:
    """Structured telemetry for a single training or validation evaluation step."""
    step: int
    train_loss: float
    train_perplexity: float
    learning_rate: float
    grad_norm: float
    tokens_seen: int
    tokens_per_second: float
    steps_per_second: float
    elapsed_seconds: float
    val_loss: Optional[float] = None
    val_perplexity: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to a dictionary."""
        return asdict(self)


class ThroughputTracker:
    """
    CPU throughput monitor tracking tokens per second and steps per second.
    """

    def __init__(self) -> None:
        self.start_time = time.perf_counter()
        self.last_step_time = self.start_time
        self.last_step_tokens = 0
        self.last_step_num = 0

    def get_rates(self, current_step: int, total_tokens: int) -> tuple[float, float, float]:
        """
        Compute instant throughput rates and total elapsed time.

        Args:
            current_step: Current global optimizer step.
            total_tokens: Total tokens processed since start.

        Returns:
            Tuple of (tokens_per_second, steps_per_second, total_elapsed_seconds).
        """
        now = time.perf_counter()
        elapsed_total = max(1e-6, now - self.start_time)
        dt = max(1e-6, now - self.last_step_time)
        d_tokens = total_tokens - self.last_step_tokens
        d_steps = current_step - self.last_step_num

        tokens_per_sec = max(0.0, d_tokens / dt)
        steps_per_sec = max(0.0, d_steps / dt)

        self.last_step_time = now
        self.last_step_tokens = total_tokens
        self.last_step_num = current_step

        return tokens_per_sec, steps_per_sec, elapsed_total
