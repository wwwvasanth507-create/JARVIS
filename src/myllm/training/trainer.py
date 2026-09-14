"""
Core CPU Training Engine for MyLLM.

Coordinates:
- Strict CPU device and artifact compatibility validation.
- Training loop with gradient accumulation, gradient clipping, AdamW, and scheduler stepping.
- Non-finite gradient/loss detection.
- Structured progress logging and telemetry tracking (tokens/sec, steps/sec).
- Periodic deterministic validation and atomic checkpointing.
- Resumption from existing checkpoints.
"""

from __future__ import annotations

import logging
import math
from pathlib import Path
import time
from typing import Any, Callable, Dict, Iterator, Optional, Tuple, Union
import torch
import torch.nn as nn
from myllm.config import AppConfig, TrainingConfig
from myllm.data.batching import BatchGenerator
from myllm.data.dataset import TokenDataset
from myllm.data.metadata import DatasetMetadata
from myllm.training.checkpoint import load_checkpoint, save_checkpoint
from myllm.training.compatibility import validate_training_compatibility
from myllm.training.experiment import ExperimentTracker
from myllm.training.metrics import ThroughputTracker, calculate_perplexity
from myllm.training.optimizer import create_optimizer
from myllm.training.scheduler import CosineWarmupScheduler
from myllm.training.state import TrainingState
from myllm.training.validation import evaluate
from myllm.utils.device import resolve_device

logger = logging.getLogger(__name__)


class TrainingError(RuntimeError):
    """Raised when training encounters an unrecoverable failure (e.g. NaN/Inf gradients)."""


class Trainer:
    """
    CPU-Only Model Training Engine.
    """

    def __init__(
        self,
        model: nn.Module,
        train_dataset: TokenDataset,
        val_dataset: Optional[TokenDataset] = None,
        config: Optional[AppConfig] = None,
        tokenizer_fingerprint: str = "",
        dataset_fingerprint: str = "",
        callbacks: Optional[list[Callable[[TrainingState], None]]] = None,
        tracker: Optional[ExperimentTracker] = None,
    ) -> None:
        self.config = config or AppConfig()
        self.train_config: TrainingConfig = self.config.training
        self.model = model
        self.train_dataset = train_dataset
        self.val_dataset = val_dataset
        self.tokenizer_fingerprint = tokenizer_fingerprint
        self.dataset_fingerprint = dataset_fingerprint
        self.callbacks = callbacks or []
        self.tracker = tracker

        # 1. Strict CPU verification
        self.device = resolve_device(self.config.system.device, strict_cpu=self.config.system.strict_cpu)
        self._verify_cpu_execution()

        # 2. Artifact compatibility checks
        self._verify_compatibility()

        # 3. Create optimizer and scheduler
        self.optimizer = create_optimizer(self.model, self.train_config)
        warmup_steps = min(self.train_config.warmup_steps, self.train_config.max_steps)
        self.scheduler = CosineWarmupScheduler(
            optimizer=self.optimizer,
            learning_rate=self.train_config.learning_rate,
            min_learning_rate=self.train_config.min_learning_rate,
            warmup_steps=warmup_steps,
            max_steps=self.train_config.max_steps,
        )

        # 4. Training state tracking
        self.state = TrainingState()
        self.throughput = ThroughputTracker()

        # 5. Checkpoint resumption if configured
        if self.train_config.resume_from:
            self._resume(self.train_config.resume_from)

    def _verify_cpu_execution(self) -> None:
        """Verify model and execution environment are strictly CPU-bound."""
        for param in self.model.parameters():
            if param.device.type != "cpu":
                raise ValueError(
                    f"Model parameter allocated on non-CPU device '{param.device}'. "
                    f"MyLLM strictly requires CPU execution."
                )

    def _verify_compatibility(self) -> None:
        """Verify model dimensions and dataset configurations are mutually compatible."""
        if len(self.train_dataset) == 0:
            raise ValueError("Training dataset has 0 valid sequence samples.")

        validate_training_compatibility(
            model=self.model,
            train_dataset=self.train_dataset,
            val_dataset=self.val_dataset,
            config=self.config,
        )

    def _resume(self, checkpoint_path: Union[str, Path]) -> None:
        """Resume training from a saved checkpoint."""
        logger.info(f"Resuming training from checkpoint: {checkpoint_path}")
        self.state, _ = load_checkpoint(
            checkpoint_path=checkpoint_path,
            model=self.model,
            optimizer=self.optimizer,
            scheduler=self.scheduler,
        )
        # Ensure scheduler max_steps respects the current run configuration
        if self.train_config.max_steps > 0:
            self.scheduler.max_steps = self.train_config.max_steps

    def train(self, target_max_steps: Optional[int] = None) -> TrainingState:
        """
        Execute the complete training loop.

        Args:
            target_max_steps: Optional step count to pause/stop early (e.g. for checkpoint interruption tests).

        Returns:
            The final TrainingState after completion.
        """
        self.model.train()
        start_step = self.state.global_step
        max_steps = target_max_steps if target_max_steps is not None else self.train_config.max_steps

        if start_step >= max_steps:
            logger.info(
                f"Training already completed (current step {start_step} >= max_steps {max_steps})."
            )
            return self.state

        logger.info(
            f"Starting training run: steps {start_step} -> {max_steps} "
            f"(batch_size={self.train_config.batch_size}, "
            f"accum_steps={self.train_config.gradient_accumulation_steps}, "
            f"device={self.device.type})"
        )

        batch_gen = BatchGenerator(
            dataset=self.train_dataset,
            batch_size=self.train_config.batch_size,
            shuffle=True,
            seed=self.train_config.seed + self.state.epoch,
            drop_last=False,
        )
        batch_iter: Iterator[Tuple[torch.Tensor, torch.Tensor]] = iter(batch_gen)

        # If resuming mid-epoch, fast-forward iterator to match consumed micro-steps
        batches_in_epoch = len(batch_gen)
        if batches_in_epoch > 0 and self.state.micro_step > 0:
            batches_to_skip = self.state.micro_step % batches_in_epoch
            for _ in range(batches_to_skip):
                try:
                    next(batch_iter)
                except StopIteration:
                    break

        accum_steps = self.train_config.gradient_accumulation_steps
        ckpt_dir = Path(self.config.paths.checkpoint_dir)

        while self.state.global_step < max_steps:
            self.optimizer.zero_grad(set_to_none=True)
            accum_loss = 0.0

            # --- Gradient Accumulation Micro-Steps ---
            for _ in range(accum_steps):
                try:
                    input_ids, labels = next(batch_iter)
                except StopIteration:
                    # New epoch / re-seed generator
                    self.state.epoch += 1
                    batch_gen = BatchGenerator(
                        dataset=self.train_dataset,
                        batch_size=self.train_config.batch_size,
                        shuffle=True,
                        seed=self.train_config.seed + self.state.epoch,
                        drop_last=False,
                    )
                    batch_iter = iter(batch_gen)
                    input_ids, labels = next(batch_iter)

                # CPU tensor assertion
                if input_ids.device.type != "cpu" or labels.device.type != "cpu":
                    raise TrainingError("Encountered non-CPU batch tensor during training.")

                # Forward pass
                _, loss = self.model(input_ids, labels=labels)

                loss_val = float(loss.item())
                if not math.isfinite(loss_val):
                    raise TrainingError(
                        f"Non-finite loss ({loss_val}) encountered at step {self.state.global_step}."
                    )

                scaled_loss = loss / accum_steps
                scaled_loss.backward()

                accum_loss += loss_val
                tokens_in_batch = input_ids.numel()
                self.state.tokens_seen += tokens_in_batch
                if labels is not None:
                    target_labels = labels[:, 1:]
                    supervised_in_batch = int((target_labels != -100).sum().item())
                    self.state.supervised_tokens_seen += supervised_in_batch
                self.state.samples_seen += input_ids.size(0)
                self.state.micro_step += 1

            # --- Gradient Clipping & Optimizer Step ---
            grad_norm = torch.nn.utils.clip_grad_norm_(
                self.model.parameters(),
                max_norm=self.train_config.grad_clip_norm,
            )
            grad_norm_val = float(grad_norm.item())
            if not math.isfinite(grad_norm_val):
                raise TrainingError(
                    f"Non-finite gradient norm ({grad_norm_val}) at step {self.state.global_step}."
                )

            self.optimizer.step()
            self.state.global_step += 1

            # Advance learning rate scheduler
            current_lr = self.scheduler.step(self.state.global_step)

            # Update metrics in state
            step_loss = accum_loss / accum_steps
            self.state.train_loss = step_loss
            self.state.response_loss = step_loss
            self.state.response_perplexity = calculate_perplexity(step_loss)
            self.state.current_lr = current_lr
            self.state.grad_norm = grad_norm_val

            t_tokens_sec, t_steps_sec, elapsed = self.throughput.get_rates(
                self.state.global_step, self.state.tokens_seen
            )
            self.state.elapsed_seconds = elapsed

            # --- Periodic Logging ---
            if (
                self.state.global_step % self.train_config.log_every_steps == 0
                or self.state.global_step == max_steps
            ):
                train_ppl = calculate_perplexity(step_loss)
                logger.info(
                    f"Step {self.state.global_step:05d}/{max_steps:05d} | "
                    f"Loss: {step_loss:.4f} | "
                    f"PPL: {train_ppl:.2f} | "
                    f"LR: {current_lr:.2e} | "
                    f"GradNorm: {grad_norm_val:.3f} | "
                    f"Speed: {t_tokens_sec:,.0f} tok/s ({t_steps_sec:.1f} steps/s)"
                )
                if self.tracker:
                    self.tracker.log_step_metrics(self.state, is_val=False, is_best=False)

            # --- Periodic Validation ---
            if (
                self.val_dataset is not None
                and len(self.val_dataset) > 0
                and (
                    self.state.global_step % self.train_config.eval_every_steps == 0
                    or self.state.global_step == max_steps
                )
            ):
                val_loss, val_ppl = evaluate(
                    model=self.model,
                    val_dataset=self.val_dataset,
                    batch_size=self.train_config.batch_size,
                    eval_batches=self.train_config.eval_batches,
                    seed=self.train_config.seed,
                )
                self.state.val_loss = val_loss
                is_best = val_loss < self.state.best_val_loss

                if is_best:
                    self.state.best_val_loss = val_loss
                    self.state.best_val_perplexity = val_ppl

                logger.info(
                    f"  [Validation @ step {self.state.global_step}] "
                    f"Val Loss: {val_loss:.4f} | "
                    f"Val PPL: {val_ppl:.2f}"
                    + (" (★ New Best)" if is_best else "")
                )

                if self.tracker:
                    self.tracker.log_step_metrics(self.state, is_val=True, is_best=is_best)

                # Save best checkpoint immediately when configured
                if is_best and self.train_config.save_best:
                    save_checkpoint(
                        checkpoint_dir=ckpt_dir,
                        model=self.model,
                        optimizer=self.optimizer,
                        scheduler=self.scheduler,
                        state=self.state,
                        config=self.config,
                        tokenizer_fingerprint=self.tokenizer_fingerprint,
                        dataset_fingerprint=self.dataset_fingerprint,
                        is_best=True,
                        max_checkpoints=self.train_config.max_checkpoints,
                    )

            # --- Periodic Step Checkpoint ---
            if (
                self.state.global_step % self.train_config.checkpoint_every_steps == 0
                or self.state.global_step == max_steps
            ):
                save_checkpoint(
                    checkpoint_dir=ckpt_dir,
                    model=self.model,
                    optimizer=self.optimizer,
                    scheduler=self.scheduler,
                    state=self.state,
                    config=self.config,
                    tokenizer_fingerprint=self.tokenizer_fingerprint,
                    dataset_fingerprint=self.dataset_fingerprint,
                    is_best=False,
                    max_checkpoints=self.train_config.max_checkpoints,
                )

            # Callbacks
            for cb in self.callbacks:
                cb(self.state)

        logger.info(
            f"Training finished successfully: {self.state.global_step} steps completed in "
            f"{self.state.elapsed_seconds:.2f}s ({self.state.tokens_seen:,} tokens processed)."
        )
        return self.state
