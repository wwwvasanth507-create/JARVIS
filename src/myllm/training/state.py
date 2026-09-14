"""
Training state tracking for MyLLM.

Maintains global optimizer step, micro-step, epochs, tokens seen, learning rate,
losses, best metrics, and RNG states for exact checkpointing and resumption.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict
import random
import numpy as np
import torch


@dataclass
class TrainingState:
    """
    Mutable state representing the exact progress of model training.
    """
    global_step: int = 0
    micro_step: int = 0
    epoch: int = 0
    tokens_seen: int = 0
    supervised_tokens_seen: int = 0
    samples_seen: int = 0
    current_lr: float = 0.0
    train_loss: float = float("nan")
    val_loss: float = float("nan")
    response_loss: float = float("nan")
    response_perplexity: float = float("nan")
    best_val_loss: float = float("inf")
    best_val_perplexity: float = float("inf")
    elapsed_seconds: float = 0.0
    grad_norm: float = 0.0
    rng_state: Dict[str, Any] = field(default_factory=dict)

    def capture_rng_state(self) -> None:
        """Capture current RNG states of Python, NumPy, and PyTorch CPU."""
        self.rng_state = {
            "python": random.getstate(),
            "numpy": np.random.get_state(),
            "torch_cpu": torch.get_rng_state(),
        }

    def restore_rng_state(self) -> None:
        """Restore saved RNG states if present."""
        if not self.rng_state:
            return
        if "python" in self.rng_state:
            try:
                random.setstate(self.rng_state["python"])
            except Exception:
                pass
        if "numpy" in self.rng_state:
            try:
                np.random.set_state(self.rng_state["numpy"])
            except Exception:
                pass
        if "torch_cpu" in self.rng_state:
            try:
                torch.set_rng_state(self.rng_state["torch_cpu"])
            except Exception:
                pass

    def to_dict(self) -> Dict[str, Any]:
        """Convert state to a serializable dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TrainingState:
        """Reconstruct TrainingState from a dictionary."""
        known_fields = cls.__dataclass_fields__.keys()
        filtered = {k: v for k, v in data.items() if k in known_fields}
        return cls(**filtered)
