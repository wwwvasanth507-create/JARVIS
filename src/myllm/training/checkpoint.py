"""
Atomic Checkpointing and State Management for MyLLM.

Provides:
- Atomic checkpoint writing via temporary staging and safe renaming (zero corruption).
- Checkpoint contents: model, optimizer, scheduler, TrainingState, config, fingerprints, RNG.
- Automated step checkpoint pruning honoring max_checkpoints while preserving latest.pt and best.pt.
- Safe checkpoint loading and descriptive error handling for corrupted files.
"""

from __future__ import annotations

from datetime import datetime, timezone
import glob
import logging
import os
from pathlib import Path
import shutil
from typing import Any, Dict, List, Optional, Tuple, Union
import uuid
import torch
import torch.nn as nn
from myllm.config import AppConfig
from myllm.model.utils import count_parameters
from myllm.training.scheduler import CosineWarmupScheduler
from myllm.training.state import TrainingState

logger = logging.getLogger(__name__)

CHECKPOINT_FORMAT_VERSION = "1.0.0"


def save_checkpoint(
    checkpoint_dir: Union[str, Path],
    model: nn.Module,
    optimizer: torch.optim.Optimizer,
    scheduler: CosineWarmupScheduler,
    state: TrainingState,
    config: AppConfig,
    tokenizer_fingerprint: str = "",
    dataset_fingerprint: str = "",
    is_best: bool = False,
    max_checkpoints: int = 3,
) -> Path:
    """
    Save training checkpoint atomically to disk.

    Writes to a temporary file first, flushes to disk, and atomically renames
    to the target path. Updates latest.pt and best.pt (if is_best).
    Prunes step checkpoints exceeding max_checkpoints.

    Args:
        checkpoint_dir: Target directory for checkpoints.
        model: PyTorch model.
        optimizer: Optimizer instance.
        scheduler: Learning rate scheduler.
        state: Training state object.
        config: Full application configuration.
        tokenizer_fingerprint: SHA-256 fingerprint of tokenizer.
        dataset_fingerprint: SHA-256 fingerprint of dataset.
        is_best: Whether this checkpoint achieves the lowest validation loss so far.
        max_checkpoints: Maximum number of step_*.pt checkpoints to retain.

    Returns:
        Path to the saved step checkpoint file.
    """
    ckpt_dir = Path(checkpoint_dir)
    ckpt_dir.mkdir(parents=True, exist_ok=True)

    # Capture latest RNG state before saving
    state.capture_rng_state()

    payload = {
        "format_version": CHECKPOINT_FORMAT_VERSION,
        "saved_at": datetime.now(timezone.utc).isoformat(),
        "model_state_dict": model.state_dict(),
        "optimizer_state_dict": optimizer.state_dict(),
        "scheduler_state": scheduler.state_dict(),
        "training_state": state.to_dict(),
        "config": config.to_dict(),
        "tokenizer_fingerprint": tokenizer_fingerprint,
        "dataset_fingerprint": dataset_fingerprint,
        "model_metadata": count_parameters(model),
        "rng_state": state.rng_state,
    }

    # Format step filename: step_00000050.pt
    step_filename = f"step_{state.global_step:08d}.pt"
    step_path = ckpt_dir / step_filename

    # 1. Atomic write to temporary file
    temp_path = ckpt_dir / f".tmp_{uuid.uuid4().hex}_{step_filename}"
    try:
        torch.save(payload, temp_path)
        # Flush OS write cache if possible
        if hasattr(os, "sync"):
            os.sync()
        # Atomic rename to final step path
        os.replace(temp_path, step_path)
    finally:
        if temp_path.exists():
            try:
                temp_path.unlink()
            except Exception:
                pass

    # 2. Update latest.pt atomically
    latest_path = ckpt_dir / "latest.pt"
    latest_temp = ckpt_dir / f".tmp_{uuid.uuid4().hex}_latest.pt"
    try:
        shutil.copy2(step_path, latest_temp)
        os.replace(latest_temp, latest_path)
    finally:
        if latest_temp.exists():
            try:
                latest_temp.unlink()
            except Exception:
                pass

    # 3. Update best.pt if this is the best validation checkpoint
    if is_best:
        best_path = ckpt_dir / "best.pt"
        best_temp = ckpt_dir / f".tmp_{uuid.uuid4().hex}_best.pt"
        try:
            shutil.copy2(step_path, best_temp)
            os.replace(best_temp, best_path)
            logger.info(f"Updated best model checkpoint at: {best_path} (val_loss={state.val_loss:.4f})")
        finally:
            if best_temp.exists():
                try:
                    best_temp.unlink()
                except Exception:
                    pass

    # 4. Prune older step checkpoints
    prune_old_checkpoints(ckpt_dir, max_checkpoints=max_checkpoints)

    logger.debug(f"Saved step checkpoint: {step_path}")
    return step_path


def prune_old_checkpoints(checkpoint_dir: Union[str, Path], max_checkpoints: int = 3) -> None:
    """
    Remove oldest step_*.pt checkpoints exceeding max_checkpoints.
    Never removes latest.pt or best.pt.
    """
    if max_checkpoints <= 0:
        return

    ckpt_dir = Path(checkpoint_dir)
    step_files: List[Path] = sorted(ckpt_dir.glob("step_*.pt"))

    if len(step_files) > max_checkpoints:
        num_to_delete = len(step_files) - max_checkpoints
        for file_to_delete in step_files[:num_to_delete]:
            try:
                file_to_delete.unlink()
                logger.debug(f"Pruned older checkpoint: {file_to_delete}")
            except Exception as e:
                logger.warning(f"Could not prune checkpoint {file_to_delete}: {e}")


def load_checkpoint(
    checkpoint_path: Union[str, Path],
    model: nn.Module,
    optimizer: Optional[torch.optim.Optimizer] = None,
    scheduler: Optional[CosineWarmupScheduler] = None,
) -> Tuple[TrainingState, Dict[str, Any]]:
    """
    Load and restore training checkpoint from disk.

    Args:
        checkpoint_path: Path to checkpoint file.
        model: Model whose parameters will be restored.
        optimizer: Optional optimizer whose state will be restored.
        scheduler: Optional scheduler whose state will be restored.

    Returns:
        Tuple of (restored_training_state, checkpoint_metadata_dict).

    Raises:
        FileNotFoundError: If checkpoint file does not exist.
        ValueError: If checkpoint format is invalid or corrupted.
    """
    path = Path(checkpoint_path)
    if not path.is_file():
        raise FileNotFoundError(f"Checkpoint file not found: {path}")

    try:
        payload = torch.load(path, map_location="cpu", weights_only=False)
    except Exception as e:
        raise ValueError(f"Failed to parse checkpoint file at {path}. File may be corrupted: {e}") from e

    if not isinstance(payload, dict):
        raise ValueError(f"Corrupt checkpoint at {path}: expected dict payload, got {type(payload)}")

    required_keys = ["model_state_dict", "training_state"]
    for key in required_keys:
        if key not in payload:
            raise ValueError(f"Corrupt checkpoint at {path}: missing required key '{key}'")

    # 1. Restore model weights
    try:
        model.load_state_dict(payload["model_state_dict"])
    except Exception as e:
        raise ValueError(f"Failed to restore model weights from {path}: {e}") from e

    # 2. Restore optimizer state if supplied
    if optimizer is not None and "optimizer_state_dict" in payload:
        try:
            optimizer.load_state_dict(payload["optimizer_state_dict"])
        except Exception as e:
            logger.warning(f"Failed to restore optimizer state from {path}: {e}")

    # 3. Restore scheduler state if supplied
    if scheduler is not None and "scheduler_state" in payload:
        try:
            scheduler.load_state_dict(payload["scheduler_state"])
        except Exception as e:
            logger.warning(f"Failed to restore scheduler state from {path}: {e}")

    # 4. Restore TrainingState
    state = TrainingState.from_dict(payload["training_state"])
    if "rng_state" in payload and payload["rng_state"]:
        state.rng_state = payload["rng_state"]
        state.restore_rng_state()

    logger.info(
        f"Successfully loaded checkpoint from {path} (restored at step {state.global_step}, "
        f"tokens_seen={state.tokens_seen:,}, val_loss={state.val_loss:.4f})"
    )
    return state, payload
