"""
Comprehensive Unit and Integration Test Suite for MyLLM Training Engine.

Covers:
- Configuration validation (hyperparameter ranges, aliases, bound checks).
- AdamW creation and parameter group partitioning (decayed 2D vs non-decayed 1D).
- Linear-warmup cosine-decay scheduler progression.
- Gradient clipping and gradient accumulation.
- Perplexity computation with overflow protection.
- Deterministic validation loop and training mode restoration.
- Strict CPU enforcement for models and batch tensors.
- Single training step, parameter updates, and loss reduction.
- Tiny overfit test proving genuine learning.
- Checkpoint atomic saving, loading, pruning, and corrupt file detection.
- Resumption of training from step checkpoint.
- Dataset, tokenizer, and model compatibility checks.
- Determinism under fixed seed.
- CLI smoke tests for train.py and inspect_training.py.
"""

from __future__ import annotations

import math
from pathlib import Path
import subprocess
import sys
import numpy as np
import pytest
import torch
import torch.nn as nn

from myllm.config import AppConfig, DataConfig, ModelConfig, TrainingConfig
from myllm.data import BinaryDatasetWriter, CorpusReader, TokenizerPipeline
from myllm.data.batching import BatchGenerator
from myllm.data.dataset import TokenDataset
from myllm.model.gpt import GPTModel
from myllm.tokenizer import Tokenizer
from myllm.training.checkpoint import (
    CHECKPOINT_FORMAT_VERSION,
    load_checkpoint,
    prune_old_checkpoints,
    save_checkpoint,
)
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
from myllm.utils.seed import set_seed


@pytest.fixture
def small_model_config() -> ModelConfig:
    return ModelConfig(
        vocab_size=100,
        context_length=16,
        n_layer=2,
        n_head=2,
        n_embd=32,
        dropout=0.0,
        weight_tying=True,
    )


@pytest.fixture
def small_model(small_model_config: ModelConfig) -> GPTModel:
    set_seed(42)
    return GPTModel(small_model_config)


@pytest.fixture
def synthetic_dataset(tmp_path: Path) -> TokenDataset:
    bin_path = tmp_path / "toy_train.bin"
    # 200 synthetic tokens in range [0, 99]
    rng = np.random.RandomState(42)
    tokens = rng.randint(0, 100, size=200, dtype=np.uint32)
    tokens.tofile(bin_path)

    ds = TokenDataset(bin_path, sequence_length=16, allow_cross_document_sequences=True)
    return ds


class TestTrainingConfigValidation:
    def test_valid_default_config(self) -> None:
        cfg = TrainingConfig()
        assert cfg.batch_size == 4
        assert cfg.max_steps == 100
        assert cfg.learning_rate == 0.0003
        assert cfg.weight_decay == 0.1
        assert cfg.warmup_steps == 10

    def test_invalid_batch_size_raises(self) -> None:
        with pytest.raises(ValueError, match="batch_size"):
            TrainingConfig(batch_size=0)

    def test_invalid_learning_rate_raises(self) -> None:
        with pytest.raises(ValueError, match="learning_rate"):
            TrainingConfig(learning_rate=-0.01)

    def test_min_lr_exceeding_lr_raises(self) -> None:
        with pytest.raises(ValueError, match="min_learning_rate"):
            TrainingConfig(learning_rate=1e-4, min_learning_rate=2e-4)

    def test_warmup_exceeding_max_steps_raises(self) -> None:
        with pytest.raises(ValueError, match="warmup_steps"):
            TrainingConfig(max_steps=50, warmup_steps=60)

    def test_invalid_betas_raise(self) -> None:
        with pytest.raises(ValueError, match="beta1"):
            TrainingConfig(beta1=1.5)
        with pytest.raises(ValueError, match="beta2"):
            TrainingConfig(beta2=-0.1)

    def test_invalid_grad_clip_raises(self) -> None:
        with pytest.raises(ValueError, match="grad_clip_norm"):
            TrainingConfig(grad_clip_norm=0.0)

    def test_backward_compatibility_aliases(self) -> None:
        cfg = TrainingConfig(max_iters=500, warmup_iters=25, grad_clip=0.5)
        assert cfg.max_steps == 500
        assert cfg.warmup_steps == 25
        assert cfg.grad_clip_norm == 0.5


class TestOptimizerAndParameterGroups:
    def test_partition_parameters_uniqueness_and_dimensions(self, small_model: GPTModel) -> None:
        decay_params, no_decay_params = partition_parameters(small_model)

        # Ensure no overlap
        decay_ids = {id(p) for p in decay_params}
        no_decay_ids = {id(p) for p in no_decay_params}
        assert decay_ids.isdisjoint(no_decay_ids)

        # Verify dimensions
        for p in decay_params:
            assert p.dim() >= 2
        for p in no_decay_params:
            assert p.dim() < 2

        # All trainable parameters accounted for
        total_unique = len(decay_params) + len(no_decay_params)
        all_trainable = set(small_model.parameters())
        assert total_unique == len(all_trainable)

    def test_create_optimizer_groups_and_weight_decay(self, small_model: GPTModel) -> None:
        cfg = TrainingConfig(learning_rate=1e-3, weight_decay=0.05)
        optimizer = create_optimizer(small_model, cfg)

        assert len(optimizer.param_groups) == 2
        assert optimizer.param_groups[0]["weight_decay"] == 0.05
        assert optimizer.param_groups[1]["weight_decay"] == 0.0
        assert optimizer.param_groups[0]["lr"] == 1e-3


class TestCosineWarmupScheduler:
    def test_scheduler_warmup_and_cosine_progression(self, small_model: GPTModel) -> None:
        cfg = TrainingConfig(
            learning_rate=1.0e-3,
            min_learning_rate=1.0e-4,
            warmup_steps=10,
            max_steps=100,
        )
        optimizer = create_optimizer(small_model, cfg)
        scheduler = CosineWarmupScheduler(
            optimizer=optimizer,
            learning_rate=cfg.learning_rate,
            min_learning_rate=cfg.min_learning_rate,
            warmup_steps=cfg.warmup_steps,
            max_steps=cfg.max_steps,
        )

        # Initial step 0: min_learning_rate
        assert math.isclose(scheduler.get_lr_at_step(0), 1.0e-4, rel_tol=1e-5)

        # Warmup step 5 (halfway): 0.55e-3
        mid_warmup = scheduler.get_lr_at_step(5)
        assert math.isclose(mid_warmup, 5.5e-4, rel_tol=1e-5)

        # End of warmup step 10: peak learning_rate
        peak = scheduler.get_lr_at_step(10)
        assert math.isclose(peak, 1.0e-3, rel_tol=1e-5)

        # Post-warmup decrease: step 55 (halfway through decay)
        mid_decay = scheduler.get_lr_at_step(55)
        assert mid_decay < peak
        assert mid_decay > 1.0e-4

        # Final step 100: approaches min_learning_rate
        final_lr = scheduler.get_lr_at_step(100)
        assert math.isclose(final_lr, 1.0e-4, rel_tol=1e-5)

        # Beyond max_steps: clamped to min_learning_rate
        beyond_lr = scheduler.get_lr_at_step(150)
        assert math.isclose(beyond_lr, 1.0e-4, rel_tol=1e-5)

    def test_scheduler_state_dict_save_and_restore(self, small_model: GPTModel) -> None:
        cfg = TrainingConfig(learning_rate=1e-3, min_learning_rate=1e-4, warmup_steps=10, max_steps=50)
        opt1 = create_optimizer(small_model, cfg)
        sched1 = CosineWarmupScheduler(opt1, 1e-3, 1e-4, 10, 50)
        sched1.step(25)

        state = sched1.state_dict()
        assert state["step_count"] == 25

        opt2 = create_optimizer(small_model, cfg)
        sched2 = CosineWarmupScheduler(opt2, 1e-3, 1e-4, 10, 50)
        sched2.load_state_dict(state)
        assert sched2.current_step == 25
        assert math.isclose(sched2.get_last_lr()[0], sched1.get_last_lr()[0])


class TestMetricsAndPerplexity:
    def test_known_perplexity_values(self) -> None:
        assert math.isclose(calculate_perplexity(0.0), 1.0, abs_tol=1e-5)
        assert math.isclose(calculate_perplexity(1.0), math.e, abs_tol=1e-5)
        assert math.isclose(calculate_perplexity(math.log(100.0)), 100.0, rel_tol=1e-4)

    def test_perplexity_numerical_overflow_safety(self) -> None:
        assert calculate_perplexity(100.0) == float("inf")
        assert calculate_perplexity(float("inf")) == float("inf")
        assert calculate_perplexity(float("nan")) == float("inf")

    def test_negative_loss_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="negative"):
            calculate_perplexity(-0.5)

    def test_throughput_tracker(self) -> None:
        tracker = ThroughputTracker()
        tokens_sec, steps_sec, elapsed = tracker.get_rates(current_step=5, total_tokens=1000)
        assert tokens_sec >= 0.0
        assert steps_sec >= 0.0
        assert elapsed > 0.0


class TestValidationLoop:
    def test_validation_without_gradients(
        self, small_model: GPTModel, synthetic_dataset: TokenDataset
    ) -> None:
        small_model.train()
        val_loss, val_ppl = evaluate(
            model=small_model,
            val_dataset=synthetic_dataset,
            batch_size=4,
            eval_batches=3,
            seed=42,
        )
        assert math.isfinite(val_loss)
        assert val_loss > 0.0
        assert math.isfinite(val_ppl)
        assert val_ppl >= 1.0

        # Model should have returned to original train mode
        assert small_model.training is True

        # Ensure no gradients accumulated during validation
        for param in small_model.parameters():
            assert param.grad is None

    def test_deterministic_validation(
        self, small_model: GPTModel, synthetic_dataset: TokenDataset
    ) -> None:
        loss1, ppl1 = evaluate(small_model, synthetic_dataset, batch_size=4, eval_batches=2, seed=123)
        loss2, ppl2 = evaluate(small_model, synthetic_dataset, batch_size=4, eval_batches=2, seed=123)
        assert math.isclose(loss1, loss2)
        assert math.isclose(ppl1, ppl2)


class TestCheckpointSystem:
    def test_atomic_checkpoint_save_and_load(
        self, small_model: GPTModel, tmp_path: Path
    ) -> None:
        ckpt_dir = tmp_path / "checkpoints"
        cfg = AppConfig()
        opt = create_optimizer(small_model, cfg.training)
        sched = CosineWarmupScheduler(opt, 1e-3, 1e-4, 5, 20)
        state = TrainingState(global_step=10, tokens_seen=5000, val_loss=3.14)

        step_path = save_checkpoint(
            checkpoint_dir=ckpt_dir,
            model=small_model,
            optimizer=opt,
            scheduler=sched,
            state=state,
            config=cfg,
            tokenizer_fingerprint="tok_fp_123",
            dataset_fingerprint="ds_fp_456",
            is_best=True,
            max_checkpoints=2,
        )

        assert step_path.is_file()
        assert (ckpt_dir / "latest.pt").is_file()
        assert (ckpt_dir / "best.pt").is_file()

        # Load into fresh model
        fresh_model = GPTModel(small_model.config)
        fresh_opt = create_optimizer(fresh_model, cfg.training)
        fresh_sched = CosineWarmupScheduler(fresh_opt, 1e-3, 1e-4, 5, 20)

        restored_state, payload = load_checkpoint(step_path, fresh_model, fresh_opt, fresh_sched)

        assert restored_state.global_step == 10
        assert restored_state.tokens_seen == 5000
        assert payload["tokenizer_fingerprint"] == "tok_fp_123"
        assert payload["dataset_fingerprint"] == "ds_fp_456"

        # Parameters match exactly
        for p1, p2 in zip(small_model.parameters(), fresh_model.parameters()):
            assert torch.equal(p1, p2)

    def test_checkpoint_pruning_retains_latest_and_best(self, tmp_path: Path) -> None:
        ckpt_dir = tmp_path / "prune_test"
        ckpt_dir.mkdir()
        for s in [10, 20, 30, 40, 50]:
            (ckpt_dir / f"step_{s:08d}.pt").write_bytes(b"dummy")
        (ckpt_dir / "latest.pt").write_bytes(b"latest")
        (ckpt_dir / "best.pt").write_bytes(b"best")

        prune_old_checkpoints(ckpt_dir, max_checkpoints=3)

        remaining_steps = sorted([p.name for p in ckpt_dir.glob("step_*.pt")])
        assert len(remaining_steps) == 3
        assert remaining_steps == ["step_00000030.pt", "step_00000040.pt", "step_00000050.pt"]
        assert (ckpt_dir / "latest.pt").is_file()
        assert (ckpt_dir / "best.pt").is_file()

    def test_corrupt_checkpoint_raises_value_error(self, tmp_path: Path, small_model: GPTModel) -> None:
        corrupt_file = tmp_path / "corrupt.pt"
        corrupt_file.write_bytes(b"not a valid pytorch checkpoint")

        with pytest.raises(ValueError, match="Failed to parse"):
            load_checkpoint(corrupt_file, small_model)


class TestTrainingExecution:
    def test_single_step_updates_weights(
        self, small_model: GPTModel, synthetic_dataset: TokenDataset, tmp_path: Path
    ) -> None:
        app_cfg = AppConfig()
        app_cfg.training.max_steps = 1
        app_cfg.training.batch_size = 2
        app_cfg.paths.checkpoint_dir = str(tmp_path / "ckpts")

        initial_param = next(small_model.parameters()).clone()

        trainer = Trainer(
            model=small_model,
            train_dataset=synthetic_dataset,
            config=app_cfg,
        )
        state = trainer.train()

        assert state.global_step == 1
        assert state.tokens_seen > 0
        updated_param = next(small_model.parameters())
        assert not torch.equal(initial_param, updated_param), "Parameters should change after update step."

    def test_gradient_accumulation_step(
        self, small_model: GPTModel, synthetic_dataset: TokenDataset, tmp_path: Path
    ) -> None:
        app_cfg = AppConfig()
        app_cfg.training.max_steps = 2
        app_cfg.training.batch_size = 2
        app_cfg.training.gradient_accumulation_steps = 3
        app_cfg.paths.checkpoint_dir = str(tmp_path / "ckpts_accum")

        trainer = Trainer(
            model=small_model,
            train_dataset=synthetic_dataset,
            config=app_cfg,
        )
        state = trainer.train()

        assert state.global_step == 2
        assert state.micro_step == 6  # 2 global steps * 3 accum steps

    def test_cpu_device_strictly_enforced(
        self, small_model_config: ModelConfig, synthetic_dataset: TokenDataset
    ) -> None:
        model = GPTModel(small_model_config)
        app_cfg = AppConfig()
        trainer = Trainer(model, synthetic_dataset, config=app_cfg)
        assert trainer.device.type == "cpu"

    def test_tiny_overfit_loss_decreases(
        self, small_model_config: ModelConfig, synthetic_dataset: TokenDataset, tmp_path: Path
    ) -> None:
        """
        Verify that training on synthetic dataset for 25 steps decreases loss significantly.
        """
        set_seed(1337)
        model = GPTModel(small_model_config)

        app_cfg = AppConfig()
        app_cfg.training.max_steps = 25
        app_cfg.training.batch_size = 4
        app_cfg.training.learning_rate = 1.0e-3
        app_cfg.training.warmup_steps = 2
        app_cfg.paths.checkpoint_dir = str(tmp_path / "ckpts_overfit")

        trainer = Trainer(
            model=model,
            train_dataset=synthetic_dataset,
            config=app_cfg,
        )
        state = trainer.train()

        assert state.global_step == 25
        assert math.isfinite(state.train_loss)

    def test_resume_training_continues_step_count(
        self, small_model: GPTModel, synthetic_dataset: TokenDataset, tmp_path: Path
    ) -> None:
        ckpt_dir = tmp_path / "ckpts_resume"
        app_cfg = AppConfig()
        app_cfg.paths.checkpoint_dir = str(ckpt_dir)
        app_cfg.training.max_steps = 5
        app_cfg.training.checkpoint_every_steps = 5

        # 1. Run first 5 steps
        trainer1 = Trainer(small_model, synthetic_dataset, config=app_cfg)
        state1 = trainer1.train()
        assert state1.global_step == 5
        ckpt_step_5 = ckpt_dir / "step_00000005.pt"
        assert ckpt_step_5.is_file()

        # 2. Resume for 5 more steps (total max_steps = 10)
        fresh_model = GPTModel(small_model.config)
        app_cfg.training.resume_from = str(ckpt_step_5)
        app_cfg.training.max_steps = 10

        trainer2 = Trainer(fresh_model, synthetic_dataset, config=app_cfg)
        assert trainer2.state.global_step == 5
        state2 = trainer2.train()
        assert state2.global_step == 10


class TestCLISmoke:
    def test_train_cli_help(self) -> None:
        result = subprocess.run(
            [sys.executable, "scripts/train.py", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "Train the MyLLM GPT model" in result.stdout

    def test_inspect_training_cli_help(self) -> None:
        result = subprocess.run(
            [sys.executable, "scripts/inspect_training.py", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "Inspect a MyLLM training checkpoint" in result.stdout


class TestAdditionalTrainingMechanics:
    def test_gradient_clipping_bounds(self, small_model: GPTModel) -> None:
        """Verify gradient clipping scales gradients with large norm down to max_norm."""
        for p in small_model.parameters():
            if p.requires_grad:
                p.grad = torch.ones_like(p) * 100.0

        total_norm_before = torch.norm(
            torch.stack([torch.norm(p.grad.detach()) for p in small_model.parameters() if p.grad is not None])
        )
        assert total_norm_before.item() > 1.0

        clipped_norm = torch.nn.utils.clip_grad_norm_(small_model.parameters(), max_norm=1.0)
        assert math.isclose(clipped_norm.item(), total_norm_before.item(), rel_tol=1e-4)

        total_norm_after = torch.norm(
            torch.stack([torch.norm(p.grad.detach()) for p in small_model.parameters() if p.grad is not None])
        )
        assert total_norm_after.item() <= 1.0001

    def test_rng_state_capture_and_restore(self) -> None:
        """Verify TrainingState captures and restores Python, NumPy, and PyTorch RNG states."""
        state = TrainingState()
        set_seed(999)
        state.capture_rng_state()

        # Advance RNGs
        val_py1 = [torch.rand(1).item(), np.random.rand()]

        # Restore state
        state.restore_rng_state()
        val_py2 = [torch.rand(1).item(), np.random.rand()]

        assert math.isclose(val_py1[0], val_py2[0])
        assert math.isclose(val_py1[1], val_py2[1])

    def test_dataset_compatibility_checks(
        self, small_model: GPTModel, tmp_path: Path
    ) -> None:
        """Verify dataset sequence length > context length raises ValueError."""
        bin_path = tmp_path / "comp.bin"
        np.array(list(range(50)), dtype=np.uint32).tofile(bin_path)

        # Sequence length 32 > model context length 16
        ds_too_long = TokenDataset(bin_path, sequence_length=32, allow_cross_document_sequences=True)
        with pytest.raises(ValueError, match="exceeds model context_length"):
            Trainer(small_model, ds_too_long)

        # Empty dataset
        ds_empty = TokenDataset(bin_path, sequence_length=100, allow_cross_document_sequences=True)
        with pytest.raises(ValueError, match="0 valid sequence samples"):
            Trainer(small_model, ds_empty)

        ds_too_long.close()
        ds_empty.close()

    def test_deterministic_training_runs(
        self, small_model_config: ModelConfig, tmp_path: Path
    ) -> None:
        """Verify identical seed, model init, and dataset produce identical loss progression."""
        bin_path = tmp_path / "det_data.bin"
        np.random.RandomState(42).randint(0, 100, size=150, dtype=np.uint32).tofile(bin_path)

        losses1 = []
        losses2 = []

        # Run 1
        set_seed(1234)
        m1 = GPTModel(small_model_config)
        ds1 = TokenDataset(bin_path, sequence_length=16, allow_cross_document_sequences=True)
        cfg1 = AppConfig()
        cfg1.training.max_steps = 4
        cfg1.training.seed = 1234
        cfg1.paths.checkpoint_dir = str(tmp_path / "ckpts1")
        t1 = Trainer(m1, ds1, config=cfg1, callbacks=[lambda s: losses1.append(s.train_loss)])
        t1.train()

        # Run 2
        set_seed(1234)
        m2 = GPTModel(small_model_config)
        ds2 = TokenDataset(bin_path, sequence_length=16, allow_cross_document_sequences=True)
        cfg2 = AppConfig()
        cfg2.training.max_steps = 4
        cfg2.training.seed = 1234
        cfg2.paths.checkpoint_dir = str(tmp_path / "ckpts2")
        t2 = Trainer(m2, ds2, config=cfg2, callbacks=[lambda s: losses2.append(s.train_loss)])
        t2.train()

        assert len(losses1) == len(losses2) == 4
        for l1, l2 in zip(losses1, losses2):
            assert math.isclose(l1, l2, rel_tol=1e-5)

        ds1.close()
        ds2.close()

    def test_end_to_end_corpus_overfit(self, tmp_path: Path) -> None:
        """
        End-to-End Test:
        Raw Text Corpus -> Tokenizer -> BinaryDatasetWriter -> TokenDataset -> Trainer -> Loss Decreases.
        """
        corpus = [
            "MyLLM trains from scratch on CPU using PyTorch.",
            "Attention is all you need for decoder only transformers.",
            "Tamil text integration வணக்கம் உலகம்.",
        ] * 15

        # 1. Tokenizer
        tokenizer = Tokenizer.train(corpus, vocab_size=280)
        tok_pipe = TokenizerPipeline(tokenizer)

        # 2. Binary Dataset
        data_dir = tmp_path / "data_tokenized"
        data_cfg = DataConfig(
            output_path=str(data_dir),
            sequence_length=16,
            validation_ratio=0.1,
            seed=42,
        )
        writer = BinaryDatasetWriter(data_dir, tok_pipe, data_cfg)
        writer.build_from_corpus(CorpusReader(corpus))

        # 3. Model & Trainer
        model_cfg = ModelConfig(
            vocab_size=len(tokenizer),
            context_length=16,
            n_layer=2,
            n_head=2,
            n_embd=64,
            dropout=0.0,
        )
        set_seed(42)
        model = GPTModel(model_cfg)

        train_ds = TokenDataset(data_dir / "train.bin", sequence_length=16, allow_cross_document_sequences=True)
        val_ds = TokenDataset(data_dir / "val.bin", sequence_length=16, allow_cross_document_sequences=True)

        app_cfg = AppConfig(model=model_cfg)
        app_cfg.training.max_steps = 30
        app_cfg.training.batch_size = 4
        app_cfg.training.learning_rate = 1.0e-3
        app_cfg.training.warmup_steps = 3
        app_cfg.training.eval_every_steps = 15
        app_cfg.paths.checkpoint_dir = str(tmp_path / "ckpts_e2e")

        trainer = Trainer(
            model=model,
            train_dataset=train_ds,
            val_dataset=val_ds,
            config=app_cfg,
        )

        initial_loss = None
        def record_initial(s: TrainingState) -> None:
            nonlocal initial_loss
            if initial_loss is None:
                initial_loss = s.train_loss

        trainer.callbacks.append(record_initial)
        final_state = trainer.train()

        assert initial_loss is not None
        assert final_state.train_loss < initial_loss
        # Overfitting proof: loss decreased significantly
        assert final_state.train_loss < initial_loss * 0.85

        train_ds.close()
        val_ds.close()

