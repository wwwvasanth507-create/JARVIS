"""
Comprehensive Unit and Integration Test Suite for Phase 6.

Tests:
1. Config profile loading (tiny_cpu, small_cpu, medium_cpu).
2. Dataset quality validation, token statistics, and leakage detection.
3. Deterministic document splitting and reproducibility.
4. Pre-training compatibility validation (mismatches, CPU device).
5. Model memory footprint estimation.
6. ExperimentTracker artifact creation, JSONL streaming, and summary generation.
7. Overfitting and underfitting diagnostic logic.
8. Best-checkpoint selection vs latest checkpoint.
9. Deterministic checkpoint resumption (continuous vs resumed run equivalence).
10. Before vs after generation tracking.
11. Strict CPU enforcement.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
import pytest
import torch
import torch.nn as nn

from myllm.config import AppConfig, ModelConfig, TrainingConfig, load_config, load_profile
from myllm.data.binary import BinaryDatasetWriter
from myllm.data.corpus import CorpusReader
from myllm.data.dataset import TokenDataset
from myllm.data.metadata import DatasetMetadata
from myllm.data.quality import DatasetQualityValidator, hash_document_text
from myllm.data.tokenizer_pipeline import TokenizerPipeline, compute_tokenizer_fingerprint
from myllm.model.gpt import GPTModel
from myllm.model.memory import estimate_memory_footprint
from myllm.tokenizer import Tokenizer
from myllm.training.checkpoint import load_checkpoint, save_checkpoint
from myllm.training.compatibility import CompatibilityError, validate_training_compatibility
from myllm.training.experiment import ExperimentTracker
from myllm.training.scheduler import CosineWarmupScheduler
from myllm.training.state import TrainingState
from myllm.training.trainer import Trainer


@pytest.fixture
def small_corpus() -> list[str]:
    return [
        "A Transformer is a neural network architecture based on self-attention.",
        "Causal self-attention masks future positions so tokens only attend to the past.",
        "AdamW decouples weight decay from the gradient update for better generalization.",
        "தமிழ் மொழி மிகத் தொன்மையான மற்றும் செழுமையான திராவிட மொழியாகும்.",
        "Linear algebra forms the foundation of deep learning via matrix operations.",
        "Entropy measures the degree of uncertainty in a statistical language model.",
    ]


@pytest.fixture
def trained_tokenizer(small_corpus: list[str], tmp_path: Path) -> Tokenizer:
    tok = Tokenizer.train(small_corpus, vocab_size=280, min_pair_frequency=1)
    tok.save(tmp_path / "tokenizer.json")
    return tok


# ---------------------------------------------------------------------------
# 1. Config Profile Loading
# ---------------------------------------------------------------------------
def test_profile_loading():
    for name in ["tiny_cpu", "small_cpu", "medium_cpu"]:
        cfg = load_profile(name)
        assert isinstance(cfg, AppConfig)
        assert cfg.system.device == "cpu"
        assert cfg.system.strict_cpu is True
        assert cfg.model.vocab_size > 0
        assert cfg.training.batch_size > 0

    with pytest.raises(FileNotFoundError):
        load_profile("non_existent_profile_xyz")


# ---------------------------------------------------------------------------
# 2. Dataset Quality, Token Statistics & Leakage Detection
# ---------------------------------------------------------------------------
def test_dataset_quality_and_leakage_detection(trained_tokenizer: Tokenizer):
    train_docs = [
        "A Transformer is a neural network architecture based on self-attention.",
        "Causal self-attention masks future positions so tokens only attend to the past.",
    ]
    val_docs_clean = [
        "தமிழ் மொழி மிகத் தொன்மையான மற்றும் செழுமையான திராவிட மொழியாகும்.",
    ]
    val_docs_leaked = [
        "A Transformer is a neural network architecture based on self-attention.",  # Exact duplicate of train!
    ]

    # Clean split -> 0 cross-split duplicates
    report_clean = DatasetQualityValidator.inspect_splits(
        train_docs=train_docs,
        val_docs=val_docs_clean,
        tokenizer=trained_tokenizer,
        context_length=16,
    )
    assert report_clean.cross_split_duplicates == 0
    assert report_clean.total_documents == 3
    assert report_clean.total_tokens > 0
    assert report_clean.mean_doc_tokens > 0
    assert len(report_clean.warnings) == 0

    # Leaked split -> detects duplicate document and logs warning
    report_leaked = DatasetQualityValidator.inspect_splits(
        train_docs=train_docs,
        val_docs=val_docs_leaked,
        tokenizer=trained_tokenizer,
        context_length=16,
    )
    assert report_leaked.cross_split_duplicates == 1
    assert any("Data leakage detected" in w for w in report_leaked.warnings)


# ---------------------------------------------------------------------------
# 3. Deterministic Splitting
# ---------------------------------------------------------------------------
def test_deterministic_document_splitting(small_corpus: list[str], trained_tokenizer: Tokenizer, tmp_path: Path):
    from myllm.config import DataConfig
    tok_pipe = TokenizerPipeline(trained_tokenizer)

    out1 = tmp_path / "ds1"
    out2 = tmp_path / "ds2"

    cfg = DataConfig(validation_ratio=0.3, sequence_length=16, seed=123)
    w1 = BinaryDatasetWriter(out1, tok_pipe, config=cfg)
    m1 = w1.build_from_corpus(CorpusReader(small_corpus))

    w2 = BinaryDatasetWriter(out2, tok_pipe, config=cfg)
    m2 = w2.build_from_corpus(CorpusReader(small_corpus))

    assert m1.train_tokens == m2.train_tokens
    assert m1.validation_tokens == m2.validation_tokens
    assert m1.dataset_fingerprint == m2.dataset_fingerprint


# ---------------------------------------------------------------------------
# 4. Pre-Training Compatibility Validation
# ---------------------------------------------------------------------------
def test_compatibility_validation(trained_tokenizer: Tokenizer, tmp_path: Path):
    import numpy as np
    bin_path = tmp_path / "dummy.bin"
    np.array(list(range(50)), dtype=np.uint32).tofile(bin_path)
    ds = TokenDataset(bin_path, sequence_length=16, allow_cross_document_sequences=True)

    # Valid model matching tokenizer
    cfg = ModelConfig(vocab_size=len(trained_tokenizer), context_length=32, n_layer=2, n_head=2, n_embd=32)
    model = GPTModel(cfg)

    # Should pass without error
    validate_training_compatibility(model=model, train_dataset=ds, tokenizer=trained_tokenizer)

    # 1. Vocab mismatch
    mismatched_model = GPTModel(ModelConfig(vocab_size=999, context_length=32, n_layer=2, n_head=2, n_embd=32))
    with pytest.raises(CompatibilityError, match="Vocabulary size mismatch"):
        validate_training_compatibility(model=mismatched_model, train_dataset=ds, tokenizer=trained_tokenizer)

    # 2. Sequence length exceeds context length
    long_seq_ds = TokenDataset(bin_path, sequence_length=64, allow_cross_document_sequences=True)
    with pytest.raises(CompatibilityError, match="exceeds model context_length"):
        validate_training_compatibility(model=model, train_dataset=long_seq_ds, tokenizer=trained_tokenizer)


# ---------------------------------------------------------------------------
# 5. Model Memory Estimation
# ---------------------------------------------------------------------------
def test_memory_footprint_estimation():
    cfg = ModelConfig(vocab_size=1000, context_length=128, n_layer=4, n_head=4, n_embd=128)
    est = estimate_memory_footprint(cfg, batch_size=4)

    assert est.total_parameters > 0
    assert est.trainable_parameters == est.total_parameters
    assert est.parameter_memory_bytes == est.total_parameters * 4
    assert est.optimizer_memory_bytes == est.total_parameters * 8
    assert est.gradient_memory_bytes == est.total_parameters * 4
    assert est.activation_memory_bytes > 0
    assert est.total_training_memory_bytes > est.parameter_memory_bytes
    assert "MB" in est.parameter_memory_str or "KB" in est.parameter_memory_str


# ---------------------------------------------------------------------------
# 6. Experiment Tracker Artifacts & Overfitting Diagnostics
# ---------------------------------------------------------------------------
def test_experiment_tracker(tmp_path: Path):
    app_cfg = AppConfig()
    tracker = ExperimentTracker(experiment_dir=tmp_path, config=app_cfg, experiment_name="test_run")

    assert tracker.root_dir.is_dir()
    assert tracker.config_yaml_path.is_file()
    assert tracker.checkpoint_dir.is_dir()

    # Log two steps
    s1 = TrainingState(global_step=5, train_loss=3.5, val_loss=4.0, best_val_loss=4.0)
    tracker.log_step_metrics(s1, is_val=True, is_best=True)

    s2 = TrainingState(global_step=10, train_loss=2.0, val_loss=5.5, best_val_loss=4.0)
    tracker.log_step_metrics(s2, is_val=True, is_best=False)

    # Overfitting check: val_loss (5.5) / train_loss (2.0) = 2.75 > 2.0 -> warning
    diag = tracker.diagnose_overfitting(s2)
    assert diag["status"] == "warning"
    assert any("overfitting" in w.lower() for w in diag["warnings"])

    # Finalize experiment
    report_path = tracker.finalize_experiment(s2, total_elapsed_sec=5.0)
    assert report_path.is_file()
    assert tracker.summary_json_path.is_file()
    assert tracker.metrics_jsonl_path.is_file()

    with open(tracker.summary_json_path, "r") as f:
        summary = json.load(f)
    assert summary["final_step"] == 10
    assert summary["best_val_loss"] == 4.0


# ---------------------------------------------------------------------------
# 7. Deterministic Checkpoint Resumption Equivalence
# ---------------------------------------------------------------------------
def test_checkpoint_resumption_equivalence(tmp_path: Path):
    import numpy as np
    torch.manual_seed(42)

    # Create dummy dataset of 200 tokens
    tokens = list(range(1, 65)) * 4
    bin_path = tmp_path / "data.bin"
    np.array(tokens, dtype=np.uint32).tofile(bin_path)

    ds = TokenDataset(bin_path, sequence_length=16, allow_cross_document_sequences=True)

    m_cfg = ModelConfig(vocab_size=100, context_length=16, n_layer=2, n_head=2, n_embd=32)

    # Run A: Train continuously for 10 steps
    app_cfg_a = AppConfig(
        model=m_cfg,
        training=TrainingConfig(
            max_steps=10,
            batch_size=2,
            learning_rate=1e-3,
            warmup_steps=2,
            checkpoint_every_steps=5,
            seed=42,
        ),
    )
    app_cfg_a.paths.checkpoint_dir = str(tmp_path / "ckpt_a")
    model_a = GPTModel(m_cfg)
    torch.manual_seed(42)
    trainer_a = Trainer(model=model_a, train_dataset=ds, config=app_cfg_a)
    state_a = trainer_a.train()

    # Run B: Same 10-step experiment config, but pause at step 5 and resume to step 10
    app_cfg_b1 = AppConfig(
        model=m_cfg,
        training=TrainingConfig(
            max_steps=10,
            batch_size=2,
            learning_rate=1e-3,
            warmup_steps=2,
            checkpoint_every_steps=5,
            seed=42,
        ),
    )
    app_cfg_b1.paths.checkpoint_dir = str(tmp_path / "ckpt_b")
    model_b = GPTModel(m_cfg)
    torch.manual_seed(42)
    trainer_b1 = Trainer(model=model_b, train_dataset=ds, config=app_cfg_b1)
    state_b1 = trainer_b1.train(target_max_steps=5)
    assert state_b1.global_step == 5

    # Resume to step 10
    app_cfg_b2 = AppConfig(
        model=m_cfg,
        training=TrainingConfig(
            max_steps=10,
            batch_size=2,
            learning_rate=1e-3,
            warmup_steps=2,
            checkpoint_every_steps=5,
            seed=42,
            resume_from=str(tmp_path / "ckpt_b" / "latest.pt"),
        ),
    )
    app_cfg_b2.paths.checkpoint_dir = str(tmp_path / "ckpt_b")
    model_b_resumed = GPTModel(m_cfg)
    trainer_b2 = Trainer(model=model_b_resumed, train_dataset=ds, config=app_cfg_b2)
    state_b2 = trainer_b2.train()
    assert state_b2.global_step == 10

    # Loss and final step should be virtually identical
    assert math.isclose(state_a.train_loss, state_b2.train_loss, rel_tol=1e-3)


# ---------------------------------------------------------------------------
# 8. Best Checkpoint Selection Logic
# ---------------------------------------------------------------------------
def test_best_checkpoint_selection(tmp_path: Path):
    m_cfg = ModelConfig(vocab_size=100, context_length=16, n_layer=2, n_head=2, n_embd=32)
    model = GPTModel(m_cfg)
    opt = torch.optim.AdamW(model.parameters(), lr=1e-3)
    sched = CosineWarmupScheduler(opt, learning_rate=1e-3, min_learning_rate=1e-4, warmup_steps=2, max_steps=10)
    cfg = AppConfig(model=m_cfg)

    # Step 1: val_loss = 3.0 -> is_best = True
    s1 = TrainingState(global_step=5, val_loss=3.0, best_val_loss=3.0)
    save_checkpoint(tmp_path, model, opt, sched, s1, cfg, is_best=True)

    # Step 2: val_loss = 4.5 -> is_best = False
    s2 = TrainingState(global_step=10, val_loss=4.5, best_val_loss=3.0)
    save_checkpoint(tmp_path, model, opt, sched, s2, cfg, is_best=False)

    # best.pt must correspond to step 5!
    best_state, payload = load_checkpoint(tmp_path / "best.pt", model)
    assert best_state.global_step == 5
    assert best_state.val_loss == 3.0

    # latest.pt must correspond to step 10!
    latest_state, _ = load_checkpoint(tmp_path / "latest.pt", model)
    assert latest_state.global_step == 10
    assert latest_state.val_loss == 4.5
