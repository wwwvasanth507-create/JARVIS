"""
CLI script for benchmarking CPU inference latency and KV cache speedup.

Example:
    python scripts/benchmark_inference.py \\
        --checkpoint checkpoints/best.pt \\
        --tokenizer data/tokenized/tokenizer.json \\
        --max-new-tokens 50
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

# Add src to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from myllm.config import ModelConfig
from myllm.inference.benchmark import benchmark_inference
from myllm.inference.loader import load_inference_system
from myllm.model.gpt import GPTModel
from myllm.utils.device import resolve_device


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark MyLLM CPU inference and KV cache performance.")
    parser.add_argument("--checkpoint", type=str, default=None, help="Path to checkpoint (.pt).")
    parser.add_argument("--tokenizer", type=str, default=None, help="Path to tokenizer.json.")
    parser.add_argument("--max-new-tokens", type=int, default=40, help="Tokens to generate during benchmark.")
    parser.add_argument("--prompt-length", type=int, default=16, help="Prompt length if synthetic prompt used.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    _ = resolve_device("cpu")  # Verify strict CPU

    if args.checkpoint and Path(args.checkpoint).is_file():
        print(f"Loading checkpoint: {args.checkpoint}")
        model, tokenizer, _ = load_inference_system(
            checkpoint_path=args.checkpoint,
            tokenizer_path=args.tokenizer,
        )
        if tokenizer is not None:
            prompt_ids = tokenizer.encode("The history of science shows that")
            max_allowed_prompt = max(1, model.config.context_length - args.max_new_tokens)
            prompt_ids = prompt_ids[:max_allowed_prompt]
            if len(prompt_ids) == 0:
                prompt_ids = [1]
        else:
            max_allowed_prompt = max(1, model.config.context_length - args.max_new_tokens)
            prompt_len = min(args.prompt_length, max_allowed_prompt)
            prompt_ids = list(range(10, 10 + prompt_len))
    else:
        print("Using synthetic small model for CPU benchmark...")
        cfg = ModelConfig(
            vocab_size=256,
            context_length=128,
            n_layer=4,
            n_head=4,
            n_embd=128,
        )
        model = GPTModel(cfg)
        tokenizer = None
        prompt_ids = list(range(10, 10 + args.prompt_length))

    print(f"\nRunning benchmark on CPU ({args.max_new_tokens} new tokens)...")
    res = benchmark_inference(
        model=model,
        prompt_ids=prompt_ids,
        max_new_tokens=args.max_new_tokens,
        tokenizer=tokenizer,
    )

    print("=" * 60)
    print("MYLLM CPU INFERENCE BENCHMARK RESULTS")
    print("=" * 60)
    print(f"Execution Device:              CPU")
    print(f"Prompt Length:                 {res.prompt_length} tokens")
    print(f"Prompt Processing Latency:     {res.prompt_eval_latency_sec * 1000:.2f} ms")
    print(f"New Tokens Generated:          {res.new_tokens_requested}")
    print("-" * 60)
    print(f"Without KV Cache (Naive):")
    print(f"  Generation Latency:          {res.naive_generation_time_sec:.3f} s")
    print(f"  Throughput:                  {res.naive_tokens_per_sec:.2f} tokens/s")
    print("-" * 60)
    print(f"With KV Cache:")
    print(f"  Generation Latency:          {res.cached_generation_time_sec:.3f} s")
    print(f"  Throughput:                  {res.cached_tokens_per_sec:.2f} tokens/s")
    print("-" * 60)
    print(f"KV Cache Speedup:              {res.speedup:.2f}x")
    print(f"Outputs Match Exactly:         {res.outputs_match}")
    print("=" * 60)


if __name__ == "__main__":
    main()
