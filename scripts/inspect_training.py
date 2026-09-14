"""
Checkpoint Inspection CLI Tool for MyLLM.

Inspects a training checkpoint (.pt file) and prints metadata, hyperparameters,
training state, validation metrics, and parameter statistics without running training.

Usage:
    python scripts/inspect_training.py --checkpoint checkpoints/latest.pt
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
import torch

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect a MyLLM training checkpoint file.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--checkpoint",
        type=str,
        required=True,
        help="Path to training checkpoint file (.pt).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    ckpt_path = Path(args.checkpoint)

    if not ckpt_path.is_file():
        print(f"ERROR: Checkpoint file not found: {ckpt_path}", file=sys.stderr)
        return 1

    try:
        payload = torch.load(ckpt_path, map_location="cpu", weights_only=False)
    except Exception as e:
        print(f"ERROR: Failed to load checkpoint: {e}", file=sys.stderr)
        return 1

    if not isinstance(payload, dict):
        print(f"ERROR: Checkpoint payload is not a dictionary: {type(payload)}", file=sys.stderr)
        return 1

    print("=" * 65)
    print("                 MyLLM Checkpoint Inspector                     ")
    print("=" * 65)
    print(f"File Path               : {ckpt_path.resolve()}")
    print(f"File Size               : {ckpt_path.stat().st_size / (1024 * 1024):.2f} MB")
    print(f"Format Version          : {payload.get('format_version', 'Unknown')}")
    print(f"Creation Timestamp      : {payload.get('saved_at', 'Unknown')}")

    # Model Metadata
    model_meta = payload.get("model_metadata", {})
    print("-" * 65)
    print("--- Model Architecture & Parameters ---")
    if model_meta:
        print(f"Total Parameters        : {model_meta.get('total', 0):,}")
        print(f"Trainable Parameters    : {model_meta.get('trainable', 0):,}")
        print(f"Tied Parameters         : {model_meta.get('tied', 0):,}")
        print(f"Memory Size (float32)   : {model_meta.get('size_mb', 0):.2f} MB")

    cfg = payload.get("config", {})
    m_cfg = cfg.get("model", {})
    if m_cfg:
        print(f"Layers (n_layer)        : {m_cfg.get('n_layer')}")
        print(f"Attention Heads (n_head): {m_cfg.get('n_head')}")
        print(f"Embedding Dim (n_embd)  : {m_cfg.get('n_embd')}")
        print(f"Context Length          : {m_cfg.get('context_length')}")
        print(f"Vocab Size              : {m_cfg.get('vocab_size')}")
        print(f"Weight Tying            : {m_cfg.get('weight_tying')}")

    # Training State
    state = payload.get("training_state", {})
    print("-" * 65)
    print("--- Training State Progress ---")
    if state:
        print(f"Global Optimizer Step   : {state.get('global_step', 0):,}")
        print(f"Micro-Steps             : {state.get('micro_step', 0):,}")
        print(f"Epoch                   : {state.get('epoch', 0)}")
        print(f"Tokens Processed        : {state.get('tokens_seen', 0):,}")
        print(f"Samples Processed       : {state.get('samples_seen', 0):,}")
        print(f"Latest Learning Rate    : {state.get('current_lr', 0.0):.2e}")
        print(f"Latest Train Loss       : {state.get('train_loss', float('nan')):.4f}")
        print(f"Latest Gradient Norm    : {state.get('grad_norm', 0.0):.3f}")
        print(f"Best Validation Loss    : {state.get('best_val_loss', float('inf')):.4f}")
        print(f"Best Val Perplexity     : {state.get('best_val_perplexity', float('inf')):.2f}")
        print(f"Total Elapsed Time      : {state.get('elapsed_seconds', 0.0):.2f}s")

    # Hyperparameters
    t_cfg = cfg.get("training", {})
    print("-" * 65)
    print("--- Training Hyperparameters ---")
    if t_cfg:
        print(f"Target Max Steps        : {t_cfg.get('max_steps')}")
        print(f"Batch Size              : {t_cfg.get('batch_size')}")
        print(f"Grad Accumulation Steps : {t_cfg.get('gradient_accumulation_steps')}")
        print(f"Peak Learning Rate      : {t_cfg.get('learning_rate')}")
        print(f"Min Learning Rate       : {t_cfg.get('min_learning_rate')}")
        print(f"Warmup Steps            : {t_cfg.get('warmup_steps')}")
        print(f"Weight Decay            : {t_cfg.get('weight_decay')}")
        print(f"Grad Clip Norm          : {t_cfg.get('grad_clip_norm')}")

    # Artifact Fingerprints
    print("-" * 65)
    print("--- Fingerprints ---")
    tok_fp = payload.get("tokenizer_fingerprint", "")
    ds_fp = payload.get("dataset_fingerprint", "")
    print(f"Tokenizer Fingerprint   : {tok_fp if tok_fp else 'None'}")
    print(f"Dataset Fingerprint     : {ds_fp if ds_fp else 'None'}")

    print("=" * 65)
    return 0


if __name__ == "__main__":
    sys.exit(main())
