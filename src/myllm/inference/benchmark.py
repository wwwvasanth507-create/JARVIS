"""
Inference Benchmarking Utilities for MyLLM.

Measures prompt processing latency, token generation latency, throughput
(tokens/sec), and compares naive vs KV-cached CPU performance.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import time
from typing import Any, Dict, List, Optional, Union
import torch
from myllm.inference.generator import Generator
from myllm.inference.types import GenerationConfig
from myllm.model.gpt import GPTModel
from myllm.tokenizer import Tokenizer


@dataclass
class BenchmarkResult:
    """Structured metrics comparing naive and KV-cached generation."""
    prompt_length: int
    new_tokens_requested: int
    prompt_eval_latency_sec: float
    naive_generation_time_sec: float
    naive_tokens_per_sec: float
    cached_generation_time_sec: float
    cached_tokens_per_sec: float
    speedup: float
    tokens_generated_naive: int
    tokens_generated_cached: int
    outputs_match: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def benchmark_inference(
    model: GPTModel,
    prompt_ids: List[int],
    max_new_tokens: int = 50,
    tokenizer: Optional[Tokenizer] = None,
    warmup_runs: int = 1,
) -> BenchmarkResult:
    """
    Run CPU inference benchmark comparing naive vs KV-cached generation.

    Args:
        model: GPTModel instance.
        prompt_ids: List of integer token IDs for the benchmark prompt.
        max_new_tokens: Number of tokens to generate.
        tokenizer: Optional Tokenizer instance.
        warmup_runs: Number of warm-up iterations before measuring.

    Returns:
        BenchmarkResult with performance metrics and speedup ratio.
    """
    generator = Generator(model=model, tokenizer=tokenizer, device="cpu")

    # Greedy config for deterministic comparison
    cfg_naive = GenerationConfig(
        max_new_tokens=max_new_tokens,
        do_sample=False,
        use_cache=False,
        stop_on_eos=False,
    )
    cfg_cached = GenerationConfig(
        max_new_tokens=max_new_tokens,
        do_sample=False,
        use_cache=True,
        stop_on_eos=False,
    )

    # Warmup
    for _ in range(warmup_runs):
        _ = generator.generate(prompt_ids, cfg_naive)
        _ = generator.generate(prompt_ids, cfg_cached)

    # 1. Prompt processing latency measurement (single forward pass over prompt)
    input_tensor = torch.tensor([prompt_ids], dtype=torch.long, device="cpu")
    t0 = time.perf_counter()
    with torch.no_grad():
        _ = model(input_tensor, use_cache=True)
    prompt_eval_latency = time.perf_counter() - t0

    # 2. Naive generation measurement
    res_naive = generator.generate(prompt_ids, cfg_naive)

    # 3. KV-cache generation measurement
    res_cached = generator.generate(prompt_ids, cfg_cached)

    speedup = (
        res_cached.tokens_per_second / res_naive.tokens_per_second
        if res_naive.tokens_per_second > 0
        else 1.0
    )
    outputs_match = res_naive.generated_token_ids == res_cached.generated_token_ids

    return BenchmarkResult(
        prompt_length=len(prompt_ids),
        new_tokens_requested=max_new_tokens,
        prompt_eval_latency_sec=prompt_eval_latency,
        naive_generation_time_sec=res_naive.generation_time,
        naive_tokens_per_sec=res_naive.tokens_per_second,
        cached_generation_time_sec=res_cached.generation_time,
        cached_tokens_per_sec=res_cached.tokens_per_second,
        speedup=speedup,
        tokens_generated_naive=res_naive.generated_tokens,
        tokens_generated_cached=res_cached.generated_tokens,
        outputs_match=outputs_match,
    )
