"""
CPU Performance Benchmark for MyLLM Chat Engine (Phase 8).

Measures prompt processing latency (prefill), autoregressive decoding latency,
throughput (tokens/sec), and compares KV cache performance against naive decoding.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
import time

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from myllm.chat import ChatEngine
from myllm.inference.types import GenerationConfig
from myllm.utils.device import resolve_device


def run_benchmark(
    checkpoint_path: str,
    tokenizer_path: str,
    num_runs: int = 3,
    max_new_tokens: int = 20,
) -> None:
    resolve_device("cpu", strict_cpu=True)

    print("=" * 65)
    print("  MyLLM Phase 8 Conversational Engine CPU Benchmark")
    print("=" * 65)

    engine = ChatEngine.from_checkpoint(
        checkpoint_path=checkpoint_path,
        tokenizer_path=tokenizer_path,
        system_prompt="You are a concise AI assistant.",
    )

    prompt = "Explain why the sky is blue in simple words."
    print(f"  Test prompt: '{prompt}'")
    print(f"  Max new tokens per run: {max_new_tokens}")
    print(f"  Number of benchmark runs: {num_runs}\n")

    for use_cache in [True, False]:
        mode_label = "WITH KV Cache" if use_cache else "WITHOUT KV Cache (Naive)"
        print(f"--- Benchmarking: {mode_label} ---")
        cfg = GenerationConfig(
            max_new_tokens=max_new_tokens,
            do_sample=False,
            use_cache=use_cache,
            stop_on_eos=False,  # force generating exactly max_new_tokens for fair timing
        )

        latencies = []
        throughputs = []
        generated_counts = []

        for r in range(num_runs):
            engine.reset()
            engine.send_user_message(prompt)

            t0 = time.perf_counter()
            resp = engine.generate_response(config=cfg)
            elapsed = time.perf_counter() - t0

            tok_count = resp.telemetry.generated_tokens
            tps = tok_count / elapsed if elapsed > 0 else 0.0

            latencies.append(elapsed)
            throughputs.append(tps)
            generated_counts.append(tok_count)
            print(f"  Run {r+1}: {tok_count} tokens in {elapsed*1000:.1f}ms ({tps:.2f} tok/s)")

        avg_latency = sum(latencies) / len(latencies)
        avg_tps = sum(throughputs) / len(throughputs)
        print(f"  => Average: {avg_latency*1000:.1f}ms | Throughput: {avg_tps:.2f} tok/s\n")

    print("=" * 65)
    print("  Benchmark completed successfully on CPU.")
    print("=" * 65)


def main() -> None:
    parser = argparse.ArgumentParser(description="MyLLM Chat Engine CPU Benchmark")
    parser.add_argument(
        "--checkpoint",
        type=str,
        default="experiments/phase7/phase7_sft_run/checkpoints/best.pt",
        help="Path to trained checkpoint",
    )
    parser.add_argument(
        "--tokenizer",
        type=str,
        default="data/tokenized/tokenizer.json",
        help="Path to tokenizer",
    )
    parser.add_argument(
        "--num-runs",
        type=int,
        default=3,
        help="Number of iterations for averaging",
    )
    parser.add_argument(
        "--max-new-tokens",
        type=int,
        default=20,
        help="Number of tokens to generate",
    )
    args = parser.parse_args()

    run_benchmark(
        checkpoint_path=args.checkpoint,
        tokenizer_path=args.tokenizer,
        num_runs=args.num_runs,
        max_new_tokens=args.max_new_tokens,
    )


if __name__ == "__main__":
    main()
