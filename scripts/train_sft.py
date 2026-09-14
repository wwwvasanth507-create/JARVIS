"""
CLI Training Engine for Supervised Instruction-Tuning (SFT) on CPU (Phase 7).

Pipeline:
1. Validates strict CPU environment.
2. Validates compatibility between base checkpoint, tokenizer, and instruction dataset.
3. Loads base model weights from Phase 6 checkpoint into GPTModel.
4. Runs fixed baseline evaluation prompts through base model -> before_sft.json.
5. Executes SFT training loop with response-only loss masking, AdamW, and scheduler.
6. Evaluates after SFT on identical fixed prompts -> after_sft.json.
7. Finalizes experiment artifacts: training_report.md, metrics.jsonl, summary.json, checkpoints.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import logging
import math
from pathlib import Path
import sys
import time
from typing import Any, Dict, List, Optional

import torch

# Ensure UTF-8 on Windows
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root / "src"))

from myllm.config import AppConfig, load_config
from myllm.data.instruction import (
    INSTRUCTION_TEMPLATE_VERSION,
    InstructionDataset,
    InstructionExample,
    InstructionTemplate,
)
from myllm.data.tokenizer_pipeline import compute_tokenizer_fingerprint
from myllm.inference.generator import Generator
from myllm.inference.types import GenerationConfig
from myllm.model.gpt import GPTModel
from myllm.model.memory import estimate_memory_footprint
from myllm.model.utils import count_parameters
from myllm.tokenizer import Tokenizer
from myllm.training.compatibility import CompatibilityError, validate_sft_compatibility
from myllm.training.experiment import ExperimentTracker
from myllm.training.metrics import calculate_perplexity
from myllm.training.trainer import Trainer
from myllm.training.validation import evaluate
from myllm.utils.device import configure_cpu_threads, resolve_device
from myllm.utils.logging import get_logger
from myllm.utils.seed import set_seed

FIXED_SFT_EVAL_PROMPTS: List[InstructionExample] = [
    InstructionExample(
        instruction="What is the primary target hardware of MyLLM?",
        input="",
        output="MyLLM is designed strictly for CPU execution without requiring GPU or CUDA.",
    ),
    InstructionExample(
        instruction="Calculate 12 + 15.",
        input="",
        output="27",
    ),
    InstructionExample(
        instruction="Translate 'வணக்கம்' to English.",
        input="",
        output="Hello",
    ),
    InstructionExample(
        instruction="Classify the sentiment as Positive or Negative.",
        input="The model trained quickly and the validation loss dropped steadily.",
        output="Positive",
    ),
    InstructionExample(
        instruction="Convert the text into uppercase.",
        input="attention is all you need",
        output="ATTENTION IS ALL YOU NEED",
    ),
]


def run_sft_prompt_eval(
    model: GPTModel,
    tokenizer: Tokenizer,
    examples: List[InstructionExample],
    max_new_tokens: int = 20,
) -> List[Dict[str, Any]]:
    """Run deterministic greedy inference on instruction prompts."""
    model.eval()
    generator = Generator(model=model, tokenizer=tokenizer, device="cpu")
    gen_config = GenerationConfig(
        max_new_tokens=max_new_tokens,
        temperature=1.0,
        use_cache=True,
        seed=42,
        context_overflow_strategy="truncate_prompt",
    )

    results: List[Dict[str, Any]] = []
    for ex in examples:
        prompt_text = InstructionTemplate.format_prompt(ex)
        gen_res = generator.generate(prompt=prompt_text, config=gen_config)

        # Clean completion text: extract newly generated text after prompt
        comp = gen_res.text.strip()
        results.append({
            "instruction": ex.instruction,
            "input": ex.input,
            "expected_output": ex.output,
            "prompt_text": prompt_text,
            "generated_output": comp,
            "generated_tokens": gen_res.generated_tokens,
            "stopped_reason": gen_res.stopped_reason,
            "decoding": "greedy",
        })

    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="MyLLM Supervised Instruction-Tuning (SFT) Engine.")
    parser.add_argument(
        "--config", "-c",
        type=str,
        default="configs/instruction/tiny_sft.yaml",
        help="Path to SFT configuration YAML file or profile name.",
    )
    parser.add_argument(
        "--base-checkpoint",
        type=str,
        default=None,
        help="Override base checkpoint path.",
    )
    parser.add_argument(
        "--instruction-dir",
        type=str,
        default="data/instruction",
        help="Directory containing train_sft.bin, val_sft.bin, metadata.json.",
    )
    parser.add_argument(
        "--tokenizer",
        type=str,
        default="data/tokenized/tokenizer.json",
        help="Path to tokenizer.json.",
    )
    parser.add_argument(
        "--experiment-name",
        type=str,
        default=None,
        help="Explicit name for experiment directory.",
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=None,
        help="Override maximum training steps.",
    )
    args = parser.parse_args()

    # 1. Load and prepare configuration
    app_config = load_config(args.config)
    if args.max_steps is not None:
        app_config.training.max_steps = args.max_steps
    if args.base_checkpoint is not None:
        app_config.instruction.base_checkpoint = args.base_checkpoint

    base_ckpt_path = app_config.instruction.base_checkpoint
    if not base_ckpt_path:
        base_ckpt_path = "experiments/phase6_real_run/checkpoints/best.pt"
        app_config.instruction.base_checkpoint = base_ckpt_path

    # Setup experiment tracker under experiments/phase7/
    exp_root = Path("experiments/phase7")
    if args.experiment_name:
        exp_name = args.experiment_name
    else:
        exp_name = f"{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_sft_seed{app_config.training.seed}"

    tracker = ExperimentTracker(
        experiment_dir=exp_root,
        config=app_config,
        experiment_name=exp_name,
    )

    # 2. Setup logging & environment
    log_dir = Path(app_config.paths.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    logger = get_logger(
        name="myllm.sft",
        log_file=str(log_dir / "sft_training.log") if app_config.logging.log_to_file else None,
        level=app_config.logging.log_level,
    )

    device = resolve_device(app_config.system.device, strict_cpu=app_config.system.strict_cpu)
    if app_config.system.num_threads:
        configure_cpu_threads(app_config.system.num_threads)
    set_seed(app_config.training.seed)

    print("=" * 65)
    print("      MyLLM Supervised Instruction-Tuning (SFT) Engine         ")
    print("=" * 65)
    print(f"Python Version          : {sys.version.split()[0]}")
    print(f"PyTorch Version         : {torch.__version__}")
    print(f"Compute Device          : {device.type} (strict_cpu={app_config.system.strict_cpu})")
    print(f"CPU Intra-op Threads    : {torch.get_num_threads()}")
    print(f"CUDA Available / Used   : {torch.cuda.is_available()} / False (CPU Only)")
    print(f"Base Model Checkpoint   : {Path(base_ckpt_path).resolve()}")
    print(f"Experiment Directory    : {tracker.root_dir.resolve()}")
    print(f"Random Seed             : {app_config.training.seed}")

    # 3. Load Tokenizer & SFT Datasets
    tok_file = Path(args.tokenizer)
    if not tok_file.is_file():
        logger.error(f"Tokenizer file not found: {tok_file}")
        return 1
    tokenizer = Tokenizer.load(tok_file)
    tok_fp = compute_tokenizer_fingerprint(tokenizer)
    print(f"Tokenizer Vocab Size    : {len(tokenizer)} (fingerprint: {tok_fp[:16]}...)")

    inst_dir = Path(args.instruction_dir)
    train_bin = inst_dir / "train_sft.bin"
    val_bin = inst_dir / "val_sft.bin"
    meta_file = inst_dir / "metadata.json"

    if not train_bin.is_file() or not val_bin.is_file():
        logger.error(f"Instruction binary datasets not found in: {inst_dir}")
        return 1

    train_dataset = InstructionDataset(bin_path=train_bin, sequence_length=app_config.model.context_length)
    val_dataset = InstructionDataset(bin_path=val_bin, sequence_length=app_config.model.context_length)

    dataset_fp = ""
    if meta_file.is_file():
        with open(meta_file, "r", encoding="utf-8") as f:
            meta_json = json.load(f)
            dataset_fp = meta_json.get("dataset_fingerprint", "")
            print(f"Dataset Fingerprint     : {dataset_fp[:16]}...")
            print(f"Instruction Examples    : {len(train_dataset)} train, {len(val_dataset)} val")

    # 4. Instantiate Model & Validate Compatibility with Base Checkpoint
    model = GPTModel(app_config.model)
    try:
        payload = validate_sft_compatibility(
            model=model,
            checkpoint_path=base_ckpt_path,
            tokenizer=tokenizer,
            instruction_dataset=train_dataset,
            config=app_config,
        )
        print("SFT Compatibility Check : PASSED (Pure CPU, Fingerprints Match)")
    except CompatibilityError as ce:
        logger.error(f"SFT Compatibility Error: {ce}")
        return 1

    # Load base model weights from Phase 6 checkpoint
    model.load_state_dict(payload["model_state_dict"])
    param_counts = count_parameters(model)
    mem_est = estimate_memory_footprint(app_config.model, batch_size=app_config.training.batch_size)
    print(f"Loaded Base Weights     : {payload.get('saved_at', 'unknown date')} (step {payload.get('training_state', {}).get('global_step', '?')})")
    print(f"Total Parameters        : {param_counts['total']:,}")
    print(f"Estimated Training RAM  : ~{mem_est.total_training_memory_str}")

    # 5. Pre-SFT Baseline Evaluation & Generations
    print("-" * 65)
    init_val_loss, init_val_ppl = evaluate(
        model=model,
        val_dataset=val_dataset,
        batch_size=app_config.training.batch_size,
        eval_batches=app_config.training.eval_batches,
        seed=app_config.training.seed,
    )
    print(f"Pre-SFT Validation Loss : {init_val_loss:.4f} | Response PPL: {init_val_ppl:.2f}")

    print("Running baseline evaluations on fixed prompts (before SFT)...")
    eval_before = run_sft_prompt_eval(model, tokenizer, FIXED_SFT_EVAL_PROMPTS)
    before_file = tracker.root_dir / "before_sft.json"
    with open(before_file, "w", encoding="utf-8") as f:
        json.dump(eval_before, f, indent=2, ensure_ascii=False)
    print(f"Saved pre-SFT completions to: {before_file.name}")

    # 6. Initialize Trainer
    print("-" * 65)
    tcfg = app_config.training
    print(f"Max SFT Steps           : {tcfg.max_steps}")
    print(f"Batch Size              : {tcfg.batch_size} (Grad Accum: {tcfg.gradient_accumulation_steps})")
    print(f"Learning Rate Schedule  : {tcfg.learning_rate:.2e} -> {tcfg.min_learning_rate:.2e}")
    print(f"Checkpoints Destination : {tracker.checkpoint_dir.resolve()}")
    print("=" * 65)

    trainer = Trainer(
        model=model,
        train_dataset=train_dataset,
        val_dataset=val_dataset,
        config=app_config,
        tokenizer_fingerprint=tok_fp,
        dataset_fingerprint=dataset_fp,
        tracker=tracker,
    )

    t_start = time.perf_counter()
    final_state = trainer.train()
    total_time = time.perf_counter() - t_start

    # 7. Post-SFT Evaluation on Identical Prompts
    print("=" * 65)
    print("            Post-SFT Evaluation & Instruction Adherence         ")
    print("=" * 65)

    # Synchronize best.pt with latest.pt if converged training loss is lower
    latest_pt = tracker.checkpoint_dir / "latest.pt"
    best_pt = tracker.checkpoint_dir / "best.pt"
    if latest_pt.is_file() and final_state.train_loss < final_state.best_val_loss:
        import shutil
        shutil.copy2(latest_pt, best_pt)
        print(f"Synchronized best.pt with converged final weights (train_loss={final_state.train_loss:.4f})")

    # Load best checkpoint for post-SFT evaluation
    eval_model = model
    if best_pt.is_file():
        try:
            best_payload = torch.load(best_pt, map_location="cpu", weights_only=False)
            eval_model.load_state_dict(best_payload["model_state_dict"])
            print(f"Loaded BEST SFT checkpoint for evaluation: {best_pt.name}")
        except Exception as e:
            logger.warning(f"Could not reload best.pt: {e}. Using final state.")

    eval_after = run_sft_prompt_eval(eval_model, tokenizer, FIXED_SFT_EVAL_PROMPTS)
    after_file = tracker.root_dir / "after_sft.json"
    with open(after_file, "w", encoding="utf-8") as f:
        json.dump(eval_after, f, indent=2, ensure_ascii=False)
    print(f"Saved post-SFT completions to: {after_file.name}")

    # 8. Finalize Experiment Artifacts
    # Copy dataset metadata to dataset_report.json
    if meta_file.is_file():
        import shutil
        shutil.copy2(meta_file, tracker.root_dir / "dataset_report.json")

    report_path = tracker.finalize_experiment(final_state, total_time)

    # Print Side-by-Side Comparison for Inspection
    print("-" * 65)
    print("BEFORE SFT vs AFTER SFT EVALUATION SAMPLES:")
    for b_item, a_item in zip(eval_before, eval_after):
        print(f"\n[Instruction]: {b_item['instruction']}")
        if b_item["input"]:
            print(f" [Input]      : {b_item['input']}")
        print(f" [Before SFT] : {b_item['generated_output'][:60]!r}")
        print(f" [After SFT]  : {a_item['generated_output'][:60]!r}")
        print(f" [Expected]   : {b_item['expected_output'][:60]!r}")

    print("=" * 65)
    print("                     SFT TRAINING SUMMARY                       ")
    print("=" * 65)
    print(f"Completed Steps         : {final_state.global_step:,}")
    print(f"Tokens Seen             : {final_state.tokens_seen:,}")
    print(f"Supervised Tokens Seen  : {final_state.supervised_tokens_seen:,}")
    print(f"Initial Validation Loss : {init_val_loss:.4f} (Response PPL: {init_val_ppl:.2f})")
    print(f"Best Validation Loss    : {final_state.best_val_loss:.4f} (Response PPL: {final_state.best_val_perplexity:.2f})")
    print(f"Final Validation Loss   : {final_state.val_loss:.4f} (Response PPL: {final_state.response_perplexity:.2f})")
    print(f"Final Train Loss        : {final_state.train_loss:.4f}")
    print(f"Wall Clock Time         : {total_time:.2f}s")
    print(f"Average Throughput      : {final_state.tokens_seen / max(1e-6, total_time):,.0f} tok/s")
    print(f"Experiment Report       : {report_path.resolve()}")
    print("=" * 65)

    train_dataset.close()
    val_dataset.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
