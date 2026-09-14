"""
Training subsystem for MyLLM.

Exposes:
- Trainer: CPU training engine.
- TrainingState: Serializable training progress tracker.
- create_optimizer: Parameter-grouped AdamW optimizer.
- CosineWarmupScheduler: Linear warmup and cosine decay scheduler.
- calculate_perplexity: Numerically safe perplexity metric.
- evaluate: Deterministic evaluation loop.
- save_checkpoint, load_checkpoint: Atomic checkpoint management and resumption.
"""

from __future__ import annotations

from myllm.training.checkpoint import (
    CHECKPOINT_FORMAT_VERSION,
    load_checkpoint,
    prune_old_checkpoints,
    save_checkpoint,
)
from myllm.training.compatibility import CompatibilityError, validate_training_compatibility
from myllm.training.experiment import ExperimentTracker
from myllm.training.metrics import (
    StepMetrics,
    ThroughputTracker,
    calculate_perplexity,
)
from myllm.training.optimizer import create_optimizer, partition_parameters
from myllm.training.scheduler import CosineWarmupScheduler
from myllm.training.state import TrainingState
from myllm.training.trainer import Trainer, TrainingError
from myllm.training.validation import evaluate

__all__ = [
    "Trainer",
    "TrainingError",
    "TrainingState",
    "create_optimizer",
    "partition_parameters",
    "CosineWarmupScheduler",
    "calculate_perplexity",
    "StepMetrics",
    "ThroughputTracker",
    "evaluate",
    "save_checkpoint",
    "load_checkpoint",
    "prune_old_checkpoints",
    "CHECKPOINT_FORMAT_VERSION",
    "CompatibilityError",
    "validate_training_compatibility",
    "ExperimentTracker",
]
