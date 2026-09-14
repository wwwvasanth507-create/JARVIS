"""
CLI script for autoregressive text generation using MyLLM.

Runs strictly on CPU.

Example:
    python scripts/generate.py \\
        --checkpoint checkpoints/best.pt \\
        --tokenizer data/tokenized/tokenizer.json \\
        --prompt "Hello world" \\
        --max-new-tokens 50 \\
        --temperature 0.8 \\
        --top-k 40 \\
        --top-p 0.9
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add src to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from myllm.inference.generator import Generator
from myllm.inference.loader import load_inference_system
from myllm.inference.types import GenerationConfig
from myllm.utils.device import resolve_device


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate text autoregressively with MyLLM on CPU.")
    parser.add_argument("--checkpoint", type=str, required=True, help="Path to model checkpoint (.pt).")
    parser.add_argument("--tokenizer", type=str, required=True, help="Path to tokenizer.json.")
    parser.add_argument("--prompt", type=str, default="Once upon a time", help="Text prompt to continue.")
    parser.add_argument("--max-new-tokens", type=int, default=50, help="Maximum number of tokens to generate.")
    parser.add_argument("--temperature", type=float, default=1.0, help="Sampling temperature (> 0).")
    parser.add_argument("--top-k", type=int, default=0, help="Top-K filtering (0 disables).")
    parser.add_argument("--top-p", type=float, default=1.0, help="Top-P nucleus filtering (1.0 disables).")
    parser.add_argument("--repetition-penalty", type=float, default=1.0, help="Repetition penalty (> 0, 1.0 disables).")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for deterministic generation.")
    parser.add_argument("--greedy", action="store_true", help="Force greedy argmax decoding.")
    parser.add_argument("--no-eos", action="store_true", help="Disable stopping on EOS token.")
    parser.add_argument("--no-cache", action="store_true", help="Disable KV cache (use naive generation).")
    parser.add_argument("--context-overflow", type=str, default="error", choices=["error", "truncate_prompt"])
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # Enforce CPU
    cpu_device = resolve_device("cpu")

    print(f"Loading checkpoint: {args.checkpoint}")
    print(f"Loading tokenizer:  {args.tokenizer}")

    model, tokenizer, metadata = load_inference_system(
        checkpoint_path=args.checkpoint,
        tokenizer_path=args.tokenizer,
    )

    generator = Generator(model=model, tokenizer=tokenizer, device=cpu_device)

    config = GenerationConfig(
        max_new_tokens=args.max_new_tokens,
        temperature=args.temperature,
        top_k=args.top_k,
        top_p=args.top_p,
        repetition_penalty=args.repetition_penalty,
        do_sample=not args.greedy,
        seed=args.seed,
        stop_on_eos=not args.no_eos,
        use_cache=not args.no_cache,
        context_overflow_strategy=args.context_overflow,
    )

    print("Generating on CPU...")
    result = generator.generate(prompt=args.prompt, config=config)

    print("\n" + "=" * 50)
    print("Prompt:")
    print(result.prompt)
    print("-" * 50)
    print("Generated:")
    print(result.text)
    print("=" * 50)
    print("Statistics:")
    print(f"  prompt tokens:    {result.prompt_tokens}")
    print(f"  generated tokens: {result.generated_tokens}")
    print(f"  total tokens:     {result.total_tokens}")
    print(f"  elapsed:          {result.generation_time:.4f} s")
    print(f"  tokens/sec:       {result.tokens_per_second:.2f}")
    print(f"  stopped reason:   {result.stopped_reason}")
    print("=" * 50)


if __name__ == "__main__":
    main()
