"""
CLI script for evaluating validation perplexity and token loss on CPU.

Example:
    python scripts/evaluate.py \\
        --checkpoint checkpoints/best.pt \\
        --tokenizer data/tokenized/tokenizer.json \\
        --dataset data/tokenized/val.bin \\
        --batch-size 4 \\
        --eval-batches 20 \\
        --seed 42
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

# Add src to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from myllm.data.dataset import TokenDataset
from myllm.data.tokenizer_pipeline import compute_tokenizer_fingerprint
from myllm.evaluation.perplexity import evaluate_perplexity
from myllm.inference.loader import load_inference_system
from myllm.utils.device import resolve_device


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate MyLLM perplexity and loss on CPU.")
    parser.add_argument("--checkpoint", type=str, required=True, help="Path to checkpoint (.pt).")
    parser.add_argument("--tokenizer", type=str, required=True, help="Path to tokenizer.json.")
    parser.add_argument("--dataset", type=str, required=True, help="Path to validation .bin dataset.")
    parser.add_argument("--batch-size", type=int, default=4, help="Batch size for evaluation.")
    parser.add_argument("--eval-batches", type=int, default=None, help="Max batches to evaluate (None for all).")
    parser.add_argument("--seed", type=int, default=42, help="Evaluation random seed.")
    return parser.parse_args()


def get_dataset_fingerprint(dataset_path: Path) -> str:
    """Retrieve dataset fingerprint from metadata or compute SHA-256."""
    meta_path = dataset_path.parent / "metadata.json"
    if meta_path.is_file():
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if "dataset_fingerprint" in data:
                return data["dataset_fingerprint"]
        except Exception:
            pass

    # Fallback to computing file hash header
    hasher = hashlib.sha256()
    with open(dataset_path, "rb") as f:
        chunk = f.read(65536)
        hasher.update(chunk)
    return hasher.hexdigest()[:16]


def main() -> None:
    args = parse_args()
    _ = resolve_device("cpu")  # Verify strict CPU

    ckpt_path = Path(args.checkpoint)
    tok_path = Path(args.tokenizer)
    data_path = Path(args.dataset)

    # 1. Load model and tokenizer
    model, tokenizer, metadata = load_inference_system(
        checkpoint_path=ckpt_path,
        tokenizer_path=tok_path,
    )

    tok_fp = compute_tokenizer_fingerprint(tokenizer) if tokenizer else "N/A"
    data_fp = get_dataset_fingerprint(data_path)

    # 2. Load dataset
    val_dataset = TokenDataset(
        bin_path=data_path,
        sequence_length=model.config.context_length,
        allow_cross_document_sequences=True,
    )

    # 3. Evaluate perplexity
    metrics = evaluate_perplexity(
        model=model,
        dataset=val_dataset,
        batch_size=args.batch_size,
        eval_batches=args.eval_batches,
        seed=args.seed,
    )

    # 4. Print structured output
    print("=" * 60)
    print("MYLLM EVALUATION RESULTS (CPU)")
    print("=" * 60)
    print(f"Model:                 GPT ({model.config.n_layer} layers, {model.config.n_head} heads, {model.config.n_embd} embd)")
    print(f"Checkpoint:            {ckpt_path.name}")
    print(f"Tokenizer fingerprint: {tok_fp[:16]}...")
    print(f"Dataset fingerprint:   {data_fp[:16]}...")
    print(f"Tokens evaluated:      {metrics.total_tokens:,}")
    print(f"Loss:                  {metrics.mean_loss:.4f}")
    print(f"Perplexity:            {metrics.perplexity:.4f}")
    print(f"Evaluation time:       {metrics.elapsed_time_sec:.3f} s")
    print(f"Tokens/sec:            {metrics.tokens_per_sec:.1f} tokens/s")
    print("=" * 60)


if __name__ == "__main__":
    main()
