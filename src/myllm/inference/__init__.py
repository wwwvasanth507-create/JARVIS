"""
Inference Subsystem for MyLLM.

Provides:
- Autoregressive text generator with KV caching (Generator).
- Sampling controls: greedy, temperature, top-k, top-p, repetition penalty.
- KVCache state management for decoder attention layers.
- Checkpoint loading and tokenizer validation (load_checkpoint_for_inference, load_inference_system).
- Stopping conditions and context validation (check_eos, validate_and_truncate_context, ContextOverflowError).
- Inference benchmarking (benchmark_inference, BenchmarkResult).
- Structured types (GenerationConfig, GenerationResult).
"""

from myllm.inference.benchmark import BenchmarkResult, benchmark_inference
from myllm.inference.cache import KVCache
from myllm.inference.generator import Generator
from myllm.inference.loader import load_checkpoint_for_inference, load_inference_system
from myllm.inference.sampling import (
    InferenceError,
    apply_repetition_penalty,
    apply_temperature,
    apply_top_k,
    apply_top_p,
    sample_next_token,
)
from myllm.inference.stopping import (
    ContextOverflowError,
    check_eos,
    validate_and_truncate_context,
)
from myllm.inference.types import GenerationConfig, GenerationResult

__all__ = [
    "GenerationConfig",
    "GenerationResult",
    "KVCache",
    "InferenceError",
    "ContextOverflowError",
    "apply_repetition_penalty",
    "apply_temperature",
    "apply_top_k",
    "apply_top_p",
    "sample_next_token",
    "check_eos",
    "validate_and_truncate_context",
    "load_checkpoint_for_inference",
    "load_inference_system",
    "Generator",
    "BenchmarkResult",
    "benchmark_inference",
]
