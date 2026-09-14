"""
Training CLI Script for MyLLM (Phase 6 Real Training Engine).

Coordinates:
- CPU hardware diagnostics & memory footprint estimation.
- Config scaling profiles (tiny_cpu, small_cpu, medium_cpu).
- Pre-training compatibility and fingerprint validation.
- Telemetry streaming to metrics.jsonl.
- Before vs After generation evaluation on fixed prompt sets.
- Best-checkpoint selection based on lowest validation loss.
- Generation of structured experiment artifacts (training_report.md, summary.json).
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import logging
import math
from pathlib import Path
import sys
import time
import torch

from myllm.config import AppConfig, ModelConfig, TrainingConfig, load_config, load_profile
from myllm.data.dataset import TokenDataset
from myllm.data.metadata import DatasetMetadata
from myllm.data.tokenizer_pipeline import compute_tokenizer_fingerprint
from myllm.inference.generator import Generator
from myllm.inference.loader import load_checkpoint_for_inference
from myllm.inference.types import GenerationConfig
from myllm.model.gpt import GPTModel
from myllm.model.memory import estimate_memory_footprint
from myllm.model.utils import count_parameters, get_model_summary
from myllm.tokenizer import Tokenizer
from myllm.training.experiment import ExperimentTracker
from myllm.training.trainer import Trainer
from myllm.training.validation import evaluate
from myllm.utils.device import configure_cpu_threads, resolve_device
from myllm.utils.logging import get_logger
from myllm.utils.seed import set_seed

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

DEFAULT_EVAL_PROMPTS = [
    "MyLLM is a pure CPU",
    "Optimization utilizes",
    "தமிழ் மொழி",
    "Deep learning architectures",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train the MyLLM GPT model strictly on CPU with experiment tracking.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to YAML configuration file or profile name.",
    )
    parser.add_argument(
        "--profile",
        type=str,
        default=None,
        choices=["tiny_cpu", "small_cpu", "medium_cpu"],
        help="Named CPU scaling profile to load.",
    )
    parser.add_argument(
        "--experiment-name",
        type=str,
        default=None,
        help="Optional custom experiment name for artifact directory.",
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


def run_prompt_eval(
    model: GPTModel,
    tokenizer: Tokenizer,
    prompts: list[str],
    max_tokens: int = 15,
) -> list[dict[str, str]]:
    """Run deterministic greedy generation across evaluation prompts."""
    generator = Generator(model=model, tokenizer=tokenizer, device="cpu")
    results = []
    for p in prompts:
        cfg = GenerationConfig(
            max_new_tokens=max_tokens,
            do_sample=False,
            stop_on_eos=False,
            context_overflow_strategy="truncate_prompt",
        )
        res = generator.generate(prompt=p, config=cfg)
        results.append({
            "prompt": p,
            "text": res.text,
            "tokens": str(res.generated_tokens),
        })
    return results


def main() -> int:
    args = parse_args()

    # 1. Load configuration or profile
    if args.profile:
        app_config = load_profile(args.profile)
        config_src = f"Profile '{args.profile}'"
    elif args.config:
        app_config = load_config(args.config)
        config_src = f"Config file '{args.config}'"
    else:
        app_config = load_config("configs/base.yaml")
        config_src = "Default 'configs/base.yaml'"

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

    # 2. Setup Experiment Tracker
    exp_root = Path(app_config.paths.experiment_dir)
    if args.experiment_name:
        exp_name = args.experiment_name
    else:
        prof_tag = args.profile or "custom"
        exp_name = f"{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{prof_tag}_seed{app_config.system.seed}"

    tracker = ExperimentTracker(
        experiment_dir=exp_root,
        config=app_config,
        experiment_name=exp_name,
    )

    # 3. Configure logging
    log_dir = Path(app_config.paths.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    logger = get_logger(
        name="myllm.training",
        log_file=str(log_dir / "training.log") if app_config.logging.log_to_file else None,
        level=app_config.logging.log_level,
    )

    print("=" * 65)
    print("           MyLLM Real CPU Training & Experiment Engine          ")
    print("=" * 65)

    # 4. CPU Hardware Verification & Reporting
    device = resolve_device(app_config.system.device, strict_cpu=app_config.system.strict_cpu)
    if app_config.system.num_threads:
        configure_cpu_threads(app_config.system.num_threads)
    set_seed(app_config.system.seed)

    print(f"Python Version          : {sys.version.split()[0]}")
    print(f"PyTorch Version         : {torch.__version__}")
    print(f"Device                  : {device.type} (strict_cpu={app_config.system.strict_cpu})")
    print(f"CPU Intra-op Threads    : {torch.get_num_threads()}")
    print(f"CUDA Available / Used   : {torch.cuda.is_available()} / False (CPU Only)")
    print(f"Configuration Source    : {config_src}")
    print(f"Experiment Directory    : {tracker.root_dir.resolve()}")
    print(f"Random Seed             : {app_config.system.seed}")

    # 5. Datasets & Tokenizer Loading
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
        if meta.tokenizer_vocab_size > 0:
            app_config.model.vocab_size = meta.tokenizer_vocab_size

    # Load and verify tokenizer
    tokenizer = None
    tok_candidate = Path(args.tokenizer) if args.tokenizer else (train_bin.parent / "tokenizer.json")
    if tok_candidate.is_file():
        tokenizer = Tokenizer.load(tok_candidate)
        calc_fp = compute_tokenizer_fingerprint(tokenizer)
        if tok_fingerprint and calc_fp != tok_fingerprint:
            logger.warning("Tokenizer fingerprint mismatch with dataset metadata!")
        tok_fingerprint = calc_fp
        print(f"Tokenizer Fingerprint   : {tok_fingerprint[:16]}...")
        app_config.model.vocab_size = len(tokenizer)

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

    # 6. Instantiate Model & Memory Estimation
    print("-" * 65)
    model = GPTModel(app_config.model)
    param_counts = count_parameters(model)
    mem_est = estimate_memory_footprint(app_config.model, batch_size=app_config.training.batch_size)

    print(f"Model Architecture      : GPTModel ({app_config.model.n_layer}L, {app_config.model.n_head}H, {app_config.model.n_embd}D)")
    print(f"Context Length          : {app_config.model.context_length}")
    print(f"Vocabulary Size         : {app_config.model.vocab_size}")
    print(f"Total Parameters        : {param_counts['total']:,}")
    print(f"Estimated Model RAM     : ~{mem_est.parameter_memory_str} (FP32 parameters)")
    print(f"Estimated Optimizer RAM : ~{mem_est.optimizer_memory_str} (AdamW state)")
    print(f"Estimated Total Budget  : ~{mem_est.total_training_memory_str} (Training)")

    # 7. Before-Training Evaluation & Generation Baseline
    print("-" * 65)
    init_val_loss = float("nan")
    init_val_ppl = float("nan")

    if val_dataset and len(val_dataset) > 0:
        init_val_loss, init_val_ppl = evaluate(
            model=model,
            val_dataset=val_dataset,
            batch_size=app_config.training.batch_size,
            eval_batches=app_config.training.eval_batches,
            seed=app_config.training.seed,
        )
        print(f"Before-Training Val Loss: {init_val_loss:.4f} | Val Perplexity: {init_val_ppl:.2f}")

    if tokenizer is not None:
        print("Running before-training baseline generation...")
        samples_before = run_prompt_eval(model, tokenizer, DEFAULT_EVAL_PROMPTS)
        tracker.save_generation_samples(samples_before, stage="before")
        print("Saved baseline completions to: generations_before.txt")

    # 8. Hyperparameters Summary
    print("-" * 65)
    tcfg = app_config.training
    print(f"Max Steps               : {tcfg.max_steps}")
    print(f"Batch Size              : {tcfg.batch_size} (Grad Accum: {tcfg.gradient_accumulation_steps})")
    print(f"Effective Batch Size    : {tcfg.batch_size * tcfg.gradient_accumulation_steps}")
    print(f"Learning Rate Schedule  : {tcfg.learning_rate:.2e} -> {tcfg.min_learning_rate:.2e} (warmup {tcfg.warmup_steps})")
    print(f"Checkpoints Location    : {tracker.checkpoint_dir.resolve()}")
    print("=" * 65)

    # 9. Initialize Trainer with Experiment Tracker
    trainer = Trainer(
        model=model,
        train_dataset=train_dataset,
        val_dataset=val_dataset,
        config=app_config,
        tokenizer_fingerprint=tok_fingerprint,
        dataset_fingerprint=dataset_fingerprint,
        tracker=tracker,
    )

    t_start = time.perf_counter()
    final_state = trainer.train()
    total_time = time.perf_counter() - t_start

    # 10. After-Training Evaluation & Best-Model Generation
    print("=" * 65)
    print("            After-Training Evaluation & Verification            ")
    print("=" * 65)

    # Load best checkpoint if available, otherwise use final model
    best_pt = tracker.checkpoint_dir / "best.pt"
    eval_model = model
    if best_pt.is_file():
        try:
            eval_model, _ = load_checkpoint_for_inference(best_pt, tokenizer=tokenizer, model_config=app_config.model)
            print(f"Loaded BEST checkpoint for final evaluation: {best_pt.name}")
        except Exception as e:
            logger.warning(f"Could not load best.pt: {e}. Using final in-memory model.")

    if tokenizer is not None:
        print("Running after-training generation on same prompts...")
        samples_after = run_prompt_eval(eval_model, tokenizer, DEFAULT_EVAL_PROMPTS)
        tracker.save_generation_samples(samples_after, stage="after")
        print("Saved trained completions to:   generations_after.txt")

    # 11. Finalize Experiment Artifacts
    report_path = tracker.finalize_experiment(final_state, total_time)

    print("=" * 65)
    print("                     TRAINING SUMMARY                           ")
    print("=" * 65)
    print(f"Completed Steps         : {final_state.global_step:,}")
    print(f"Total Tokens Processed  : {final_state.tokens_seen:,}")
    print(f"Final Train Loss        : {final_state.train_loss:.4f}")
    if math.isfinite(init_val_loss) and math.isfinite(final_state.best_val_loss):
        print(f"Validation Loss Change  : {init_val_loss:.4f} -> {final_state.best_val_loss:.4f} (Best)")
        print(f"Val Perplexity Change   : {init_val_ppl:.2f} -> {final_state.best_val_perplexity:.2f} (Best)")
    print(f"Wall Clock Elapsed Time : {total_time:.2f}s")
    print(f"Average Throughput      : {final_state.tokens_seen / max(1e-6, total_time):,.0f} tok/s")
    print(f"Experiment Report       : {report_path.resolve()}")
    print("=" * 65)

    # Close memory mapped datasets
    train_dataset.close()
    if val_dataset:
        val_dataset.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
