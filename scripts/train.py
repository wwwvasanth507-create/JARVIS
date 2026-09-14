"""
Training CLI Script for MyLLM.

Launches pure CPU model training with AdamW, linear-warmup cosine-decay scheduling,
periodic validation, atomic checkpointing, and resumption capabilities.

Usage:
    python scripts/train.py --config configs/base.yaml --train-dataset data/tokenized/train.bin
    python scripts/train.py --resume checkpoints/latest.pt
"""

from __future__ import annotations

import argparse
import logging
import math
from pathlib import Path
import sys
import time
import torch

from myllm.config import AppConfig, ModelConfig, TrainingConfig, load_config
from myllm.data.dataset import TokenDataset
from myllm.data.metadata import DatasetMetadata
from myllm.data.tokenizer_pipeline import compute_tokenizer_fingerprint
from myllm.model.gpt import GPTModel
from myllm.model.utils import count_parameters, get_model_summary
from myllm.tokenizer import Tokenizer
from myllm.training.trainer import Trainer
from myllm.utils.device import configure_cpu_threads, resolve_device
from myllm.utils.logging import get_logger
from myllm.utils.seed import set_seed

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train the MyLLM GPT model strictly on CPU.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--config",
        type=str,
        default="configs/base.yaml",
        help="Path to YAML configuration file.",
    )
    parser.add_argument(
        "--train-dataset",
        type=str,
        default="data/tokenized/train.bin",
        help="Path to binary training dataset file (.bin).",
    )
    parser.add_argument(
        "--val-dataset",
        type=str,
        default="data/tokenized/val.bin",
        help="Path to binary validation dataset file (.bin).",
    )
    parser.add_argument(
        "--tokenizer",
        type=str,
        default=None,
        help="Path to tokenizer.json for verification and fingerprinting.",
    )
    parser.add_argument(
        "--checkpoint-dir",
        type=str,
        default=None,
        help="Output directory for training checkpoints.",
    )
    parser.add_argument(
        "--resume",
        type=str,
        default=None,
        help="Path to checkpoint file (.pt) to resume training from.",
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=None,
        help="Override total training steps.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=None,
        help="Override training batch size.",
    )
    parser.add_argument(
        "--learning-rate",
        type=float,
        default=None,
        help="Override peak learning rate.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Override random seed for reproducibility.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    # 1. Load configuration
    config_path = Path(args.config)
    app_config = load_config(config_path if config_path.is_file() else None)

    # Apply CLI overrides
    if args.checkpoint_dir:
        app_config.paths.checkpoint_dir = args.checkpoint_dir
    if args.resume:
        app_config.training.resume_from = args.resume
    if args.max_steps is not None:
        app_config.training.max_steps = args.max_steps
    if args.batch_size is not None:
        app_config.training.batch_size = args.batch_size
    if args.learning_rate is not None:
        app_config.training.learning_rate = args.learning_rate
    if args.seed is not None:
        app_config.system.seed = args.seed
        app_config.training.seed = args.seed

    # 2. Configure logging
    log_dir = Path(app_config.paths.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    logger = get_logger(
        name="myllm.training",
        log_file=str(log_dir / "training.log") if app_config.logging.log_to_file else None,
        level=app_config.logging.log_level,
    )

    print("=" * 65)
    print("                    MyLLM CPU Training Engine                   ")
    print("=" * 65)

    # 3. CPU Device & Thread Verification
    device = resolve_device(app_config.system.device, strict_cpu=app_config.system.strict_cpu)
    if app_config.system.num_threads:
        configure_cpu_threads(app_config.system.num_threads)
    set_seed(app_config.system.seed)

    print(f"Device                  : {device.type} (strict_cpu={app_config.system.strict_cpu})")
    print(f"CPU Intra-op Threads    : {torch.get_num_threads()}")
    print(f"Random Seed             : {app_config.system.seed}")
    print(f"Checkpoints Path        : {app_config.paths.checkpoint_dir}")

    # 4. Load Dataset Metadata & Datasets
    train_bin = Path(args.train_dataset)
    if not train_bin.is_file():
        logger.error(f"Training dataset not found at: {train_bin}")
        return 1

    metadata_path = train_bin.parent / "metadata.json"
    tok_fingerprint = ""
    dataset_fingerprint = ""

    if metadata_path.is_file():
        meta = DatasetMetadata.load(metadata_path)
        tok_fingerprint = meta.tokenizer_fingerprint
        dataset_fingerprint = meta.dataset_fingerprint
        print(f"Dataset Tokens          : {meta.train_tokens:,} train, {meta.validation_tokens:,} val")
        print(f"Dataset Fingerprint     : {meta.dataset_fingerprint[:16]}...")
        # Match model vocab size to dataset if applicable
        if meta.tokenizer_vocab_size > 0:
            app_config.model.vocab_size = meta.tokenizer_vocab_size

    # Verify optional tokenizer
    if args.tokenizer:
        tok_path = Path(args.tokenizer)
        if tok_path.is_file():
            tok = Tokenizer.load(tok_path)
            calc_fp = compute_tokenizer_fingerprint(tok)
            if tok_fingerprint and calc_fp != tok_fingerprint:
                logger.warning("Tokenizer fingerprint does not match dataset metadata fingerprint!")
            tok_fingerprint = calc_fp

    train_dataset = TokenDataset(
        bin_path=train_bin,
        sequence_length=app_config.data.sequence_length,
        allow_cross_document_sequences=app_config.data.allow_cross_document_sequences,
    )
    print(f"Train Sequence Windows  : {len(train_dataset):,}")

    val_dataset = None
    val_bin = Path(args.val_dataset)
    if val_bin.is_file():
        val_dataset = TokenDataset(
            bin_path=val_bin,
            sequence_length=app_config.data.sequence_length,
            allow_cross_document_sequences=app_config.data.allow_cross_document_sequences,
        )
        print(f"Val Sequence Windows    : {len(val_dataset):,}")

    # 5. Instantiate Model
    print("-" * 65)
    model = GPTModel(app_config.model)
    param_counts = count_parameters(model)
    print(f"Model Architecture      : GPTModel ({app_config.model.n_layer}L, {app_config.model.n_head}H, {app_config.model.n_embd}D)")
    print(f"Context Length          : {app_config.model.context_length}")
    print(f"Vocabulary Size         : {app_config.model.vocab_size}")
    print(f"Total Parameters        : {param_counts['total']:,}")
    print(f"Trainable Parameters    : {param_counts['trainable']:,}")
    print(f"Weight Tying            : {app_config.model.weight_tying}")

    # 6. Hyperparameters Summary
    print("-" * 65)
    tcfg = app_config.training
    print(f"Max Steps               : {tcfg.max_steps}")
    print(f"Batch Size              : {tcfg.batch_size}")
    print(f"Grad Accumulation Steps : {tcfg.gradient_accumulation_steps}")
    print(f"Peak Learning Rate      : {tcfg.learning_rate}")
    print(f"Min Learning Rate       : {tcfg.min_learning_rate}")
    print(f"Warmup Steps            : {tcfg.warmup_steps}")
    print(f"Weight Decay            : {tcfg.weight_decay}")
    print(f"Grad Clip Norm          : {tcfg.grad_clip_norm}")
    print(f"Log / Eval / Checkpoint : every {tcfg.log_every_steps} / {tcfg.eval_every_steps} / {tcfg.checkpoint_every_steps} steps")
    print("=" * 65)

    # 7. Initialize Trainer & Run
    trainer = Trainer(
        model=model,
        train_dataset=train_dataset,
        val_dataset=val_dataset,
        config=app_config,
        tokenizer_fingerprint=tok_fingerprint,
        dataset_fingerprint=dataset_fingerprint,
    )

    t_start = time.perf_counter()
    final_state = trainer.train()
    total_time = time.perf_counter() - t_start

    # 8. Print Summary
    print("=" * 65)
    print("                     Training Complete                          ")
    print("=" * 65)
    print(f"Completed Steps         : {final_state.global_step:,}")
    print(f"Total Tokens Processed  : {final_state.tokens_seen:,}")
    print(f"Final Train Loss        : {final_state.train_loss:.4f}")
    if math.isfinite(final_state.best_val_loss):
        print(f"Best Validation Loss    : {final_state.best_val_loss:.4f}")
        print(f"Best Val Perplexity     : {final_state.best_val_perplexity:.2f}")
    print(f"Wall Clock Elapsed Time : {total_time:.2f}s")
    print(f"Average Throughput      : {final_state.tokens_seen / max(1e-6, total_time):,.0f} tok/s")
    print("=" * 65)

    # Clean close memory-mapped datasets
    train_dataset.close()
    if val_dataset:
        val_dataset.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
