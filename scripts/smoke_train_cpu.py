"""
Real CPU Training Smoke Run for MyLLM (Phase 4 Verification).

Demonstrates the complete end-to-end pipeline:
Corpus -> Tokenizer -> Binary Dataset -> GPTModel -> Trainer (AdamW + Cosine Warmup)
-> Validation -> Checkpoint -> Resume -> Verifies Learning.
"""

from __future__ import annotations

import math
from pathlib import Path
import shutil
import sys
import time
import torch

from myllm.config import AppConfig, DataConfig, ModelConfig, TrainingConfig
from myllm.data import BinaryDatasetWriter, CorpusReader, TokenDataset, TokenizerPipeline
from myllm.model import GPTModel
from myllm.model.utils import count_parameters
from myllm.tokenizer import Tokenizer
from myllm.training import Trainer, load_checkpoint
from myllm.utils.device import configure_cpu_threads, resolve_device
from myllm.utils.seed import set_seed

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")


def run_smoke_test() -> int:
    tmp_root = Path("data/smoke_training_run")
    shutil.rmtree(tmp_root, ignore_errors=True)
    tmp_root.mkdir(parents=True, exist_ok=True)

    print("=" * 65)
    print("           MyLLM Real CPU Training Smoke Verification           ")
    print("=" * 65)

    # 1. Setup Environment
    set_seed(42)
    device = resolve_device("cpu", strict_cpu=True)
    threads = configure_cpu_threads(4)
    print(f"Device                  : {device.type} (strict_cpu=True)")
    print(f"Active CPU Threads      : {threads}")

    # 2. Text Corpus
    corpus = [
        "MyLLM is a pure CPU decoder-only Transformer language model built from scratch.",
        "Optimization utilizes AdamW with decoupled weight decay for 2D weight matrices.",
        "LayerNorm and bias parameters receive zero weight decay to preserve representation.",
        "தமிழ் மொழி மற்றும் திருக்குறள் ஆதரவு முழுமையாக உள்ளது.",
        "Learning rate scheduling begins with linear warmup followed by smooth cosine decay.",
        "Cross-document sequence boundaries prevent contamination across documents.",
        "Atomic checkpoint writing protects training progress against unexpected interruption.",
        "Robotics 🤖 and machine intelligence 🧠 require deterministic CPU pipelines 🚀.",
    ] * 20

    print(f"Corpus Documents        : {len(corpus):,}")

    # 3. Train Tokenizer
    tok_path = tmp_root / "tokenizer.json"
    print("Training Byte-Level BPE Tokenizer...")
    tok_start = time.perf_counter()
    tokenizer = Tokenizer.train(corpus, vocab_size=320, min_pair_frequency=2)
    tokenizer.save(tok_path)
    tok_time = time.perf_counter() - tok_start
    print(f"Tokenizer Trained       : Vocab size {len(tokenizer)} in {tok_time:.3f}s")

    # 4. Build Binary Dataset
    data_dir = tmp_root / "tokenized"
    data_cfg = DataConfig(
        output_path=str(data_dir),
        sequence_length=16,
        validation_ratio=0.15,
        seed=42,
    )
    tok_pipe = TokenizerPipeline(tokenizer)
    writer = BinaryDatasetWriter(data_dir, tok_pipe, data_cfg)
    meta = writer.build_from_corpus(CorpusReader(corpus))
    print(f"Dataset Built           : {meta.train_tokens:,} train tokens, {meta.validation_tokens:,} val tokens")

    train_ds = TokenDataset(data_dir / "train.bin", sequence_length=16, allow_cross_document_sequences=True)
    val_ds = TokenDataset(data_dir / "val.bin", sequence_length=16, allow_cross_document_sequences=True)
    print(f"Valid Sequence Windows  : {len(train_ds):,} train, {len(val_ds):,} val")

    # 5. Instantiate Model
    model_cfg = ModelConfig(
        vocab_size=len(tokenizer),
        context_length=32,
        n_layer=2,
        n_head=2,
        n_embd=64,
        dropout=0.0,
        weight_tying=True,
    )
    model = GPTModel(model_cfg)
    params = count_parameters(model)
    print(f"Model Parameters        : {params['total']:,} total, {params['trainable']:,} trainable")

    # 6. Configure Trainer
    ckpt_dir = tmp_root / "checkpoints"
    app_cfg = AppConfig(
        model=model_cfg,
        training=TrainingConfig(
            batch_size=4,
            max_steps=25,
            learning_rate=0.001,
            min_learning_rate=0.0001,
            warmup_steps=5,
            weight_decay=0.1,
            grad_clip_norm=1.0,
            log_every_steps=5,
            eval_every_steps=10,
            eval_batches=5,
            checkpoint_every_steps=10,
            max_checkpoints=2,
            save_best=True,
            seed=42,
        ),
    )
    app_cfg.paths.checkpoint_dir = str(ckpt_dir)

    print("-" * 65)
    print("Starting 25-step CPU training run...")
    print("-" * 65)

    trainer = Trainer(
        model=model,
        train_dataset=train_ds,
        val_dataset=val_ds,
        config=app_cfg,
        tokenizer_fingerprint=meta.tokenizer_fingerprint,
        dataset_fingerprint=meta.dataset_fingerprint,
    )

    initial_loss = None
    def track_loss(s):
        nonlocal initial_loss
        if initial_loss is None:
            initial_loss = s.train_loss

    trainer.callbacks.append(track_loss)

    t_train_start = time.perf_counter()
    state = trainer.train()
    train_duration = time.perf_counter() - t_train_start

    print("-" * 65)
    print("Training Progress Results:")
    print(f"Initial Step Loss       : {initial_loss:.4f}")
    print(f"Final Step Loss         : {state.train_loss:.4f}")
    print(f"Best Validation Loss    : {state.best_val_loss:.4f}")
    print(f"Best Val Perplexity     : {state.best_val_perplexity:.2f}")
    print(f"Tokens Processed        : {state.tokens_seen:,}")
    print(f"Elapsed Time            : {train_duration:.2f}s")
    print(f"Average Throughput      : {state.tokens_seen / train_duration:,.0f} tok/s")

    # Verify learning occurs
    assert state.train_loss < initial_loss, "Training loss failed to decrease!"
    print("LEARNING VERIFIED       : Loss decreased successfully.")

    # 7. Verify Checkpoint Creation
    latest_pt = ckpt_dir / "latest.pt"
    best_pt = ckpt_dir / "best.pt"
    assert latest_pt.is_file(), "latest.pt was not created!"
    assert best_pt.is_file(), "best.pt was not created!"
    print("CHECKPOINTS VERIFIED    : latest.pt and best.pt confirmed.")

    # 8. Test Resumption
    print("-" * 65)
    print("Testing Checkpoint Resumption (25 -> 35 steps)...")
    fresh_model = GPTModel(model_cfg)
    app_cfg.training.resume_from = str(latest_pt)
    app_cfg.training.max_steps = 35

    trainer_resumed = Trainer(
        model=fresh_model,
        train_dataset=train_ds,
        val_dataset=val_ds,
        config=app_cfg,
        tokenizer_fingerprint=meta.tokenizer_fingerprint,
        dataset_fingerprint=meta.dataset_fingerprint,
    )
    assert trainer_resumed.state.global_step == 25, "Failed to restore step 25!"

    state_resumed = trainer_resumed.train()
    assert state_resumed.global_step == 35, "Failed to complete remaining steps!"
    print(f"RESUME VERIFIED         : Completed step {state_resumed.global_step} (loss: {state_resumed.train_loss:.4f})")

    # Clean up
    train_ds.close()
    val_ds.close()
    shutil.rmtree(tmp_root, ignore_errors=True)

    print("=" * 65)
    print("SUCCESS: Full CPU training, validation, checkpointing & resume verified.")
    print("=" * 65)
    return 0


if __name__ == "__main__":
    sys.exit(run_smoke_test())
