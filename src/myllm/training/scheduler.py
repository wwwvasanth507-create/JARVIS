"""
Learning Rate Scheduler with Linear Warmup and Cosine Decay for MyLLM.

Provides:
- Linear warmup from min_learning_rate to peak learning_rate over warmup_steps.
- Cosine decay from learning_rate down to min_learning_rate from warmup_steps to max_steps.
- Constant min_learning_rate beyond max_steps.
- Inspectable step calculation, state_dict serialization, and parameter group updates.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional
import torch.optim


class CosineWarmupScheduler:
    """
    Linear Warmup and Cosine Decay Learning Rate Scheduler.

    Schedule:
        - 0 <= step < warmup_steps:
            lr(step) = min_lr + (peak_lr - min_lr) * (step / warmup_steps)
        - warmup_steps <= step <= max_steps:
            progress = (step - warmup_steps) / (max_steps - warmup_steps)
            lr(step) = min_lr + 0.5 * (1.0 + cos(pi * progress)) * (peak_lr - min_lr)
        - step > max_steps:
            lr(step) = min_lr
    """

    def __init__(
        self,
        optimizer: torch.optim.Optimizer,
        learning_rate: float,
        min_learning_rate: float,
        warmup_steps: int,
        max_steps: int,
    ) -> None:
        if learning_rate <= 0:
            raise ValueError(f"learning_rate must be positive, got {learning_rate}")
        if min_learning_rate < 0:
            raise ValueError(f"min_learning_rate cannot be negative, got {min_learning_rate}")
        if min_learning_rate > learning_rate:
            raise ValueError(
                f"min_learning_rate ({min_learning_rate}) cannot exceed learning_rate ({learning_rate})"
            )
        if warmup_steps < 0:
            raise ValueError(f"warmup_steps cannot be negative, got {warmup_steps}")
        if max_steps <= 0:
            raise ValueError(f"max_steps must be positive, got {max_steps}")
        if warmup_steps > max_steps:
            raise ValueError(
                f"warmup_steps ({warmup_steps}) cannot exceed max_steps ({max_steps})"
            )

        self.optimizer = optimizer
        self.learning_rate = float(learning_rate)
        self.min_learning_rate = float(min_learning_rate)
        self.warmup_steps = int(warmup_steps)
        self.max_steps = int(max_steps)

        self._step_count: int = 0
        # Initialize optimizer learning rates to step 0
        self.step(0)

    def get_lr_at_step(self, step: int) -> float:
        """Calculate the scheduled learning rate at a given step index."""
        if step < 0:
            step = 0

        # 1. Warmup phase
        if self.warmup_steps > 0 and step < self.warmup_steps:
            pct = step / float(self.warmup_steps)
            return self.min_learning_rate + pct * (self.learning_rate - self.min_learning_rate)

        # 2. Beyond max_steps
        if step >= self.max_steps:
            return self.min_learning_rate

        # 3. Cosine decay phase
        decay_steps = max(1, self.max_steps - self.warmup_steps)
        progress = (step - self.warmup_steps) / float(decay_steps)
        coeff = 0.5 * (1.0 + math.cos(math.pi * progress))
        return self.min_learning_rate + coeff * (self.learning_rate - self.min_learning_rate)

    def step(self, current_step: Optional[int] = None) -> float:
        """
        Advance scheduler and update optimizer learning rate.

        Args:
            current_step: Optional explicit step index. If None, uses internal counter.

        Returns:
            The newly assigned learning rate.
        """
        if current_step is not None:
            self._step_count = current_step
        else:
            self._step_count += 1

        lr = self.get_lr_at_step(self._step_count)
        for param_group in self.optimizer.param_groups:
            param_group["lr"] = lr
        return lr

    def get_last_lr(self) -> List[float]:
        """Return the current learning rates across all optimizer parameter groups."""
        return [float(param_group["lr"]) for param_group in self.optimizer.param_groups]

    @property
    def current_step(self) -> int:
        """Current step index."""
        return self._step_count

    def state_dict(self) -> Dict[str, Any]:
        """Serialize scheduler state for checkpointing."""
        return {
            "step_count": self._step_count,
            "learning_rate": self.learning_rate,
            "min_learning_rate": self.min_learning_rate,
            "warmup_steps": self.warmup_steps,
            "max_steps": self.max_steps,
        }

    def load_state_dict(self, state_dict: Dict[str, Any]) -> None:
        """Restore scheduler state from checkpoint dictionary."""
        self._step_count = state_dict.get("step_count", 0)
        self.learning_rate = state_dict.get("learning_rate", self.learning_rate)
        self.min_learning_rate = state_dict.get("min_learning_rate", self.min_learning_rate)
        self.warmup_steps = state_dict.get("warmup_steps", self.warmup_steps)
        self.max_steps = state_dict.get("max_steps", self.max_steps)
        # Apply restored step to optimizer
        self.step(self._step_count)
