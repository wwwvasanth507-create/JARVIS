"""
Local Model Benchmarking Utility for JARVIS.
"""

import time
import json
import os
import psutil
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseModel
from jarvis.brain.provider import ModelProvider


class ModelBenchmarkMetrics(BaseModel):
    timestamp: float
    model_name: str
    backend: str
    load_duration_seconds: float
    first_token_latency_seconds: float
    total_generation_seconds: float
    tokens_generated: int
    tokens_per_second: float
    process_ram_mb: float

    @property
    def load_duration_sec(self) -> float:
        return self.load_duration_seconds

    def __getitem__(self, item: str) -> Any:
        return getattr(self, item)

    def __contains__(self, item: str) -> bool:
        return hasattr(self, item)


class ModelBenchmarkUtility:
    """
    Benchmarks local model load time, first-token latency, tokens/sec, and memory usage.
    Outputs metrics to data/cache/model-benchmark.json.
    """

    def __init__(self, cache_file: str = "data/cache/model-benchmark.json"):
        self.cache_file = Path(cache_file)

    def run_benchmark(
        self,
        provider: ModelProvider,
        prompt: str = "Hello JARVIS, report your status.",
        output_log_path: Optional[str] = None
    ) -> ModelBenchmarkMetrics:
        """Runs a short controlled benchmark on the provider."""
        if output_log_path:
            self.cache_file = Path(output_log_path)

        start_load = time.perf_counter()
        if not provider.is_ready():
            provider.load()
        load_duration = time.perf_counter() - start_load

        start_gen = time.perf_counter()
        first_token_latency = 0.0
        tokens_count = 0
        chunks = []

        try:
            req = provider.model_info()
            from jarvis.brain.models import GenerationRequest
            gen_req = GenerationRequest(prompt=prompt, max_tokens=64)

            stream_gen = provider.stream(gen_req)
            for chunk in stream_gen:
                if tokens_count == 0:
                    first_token_latency = round(time.perf_counter() - start_gen, 4)
                chunks.append(chunk)
                tokens_count += 1

            total_duration = time.perf_counter() - start_gen
            mem_info = psutil.Process(os.getpid()).memory_info()
            ram_used_mb = round(mem_info.rss / (1024 * 1024), 2)

            metrics = ModelBenchmarkMetrics(
                timestamp=time.time(),
                model_name=req.name,
                backend=req.backend,
                load_duration_seconds=round(load_duration, 4),
                first_token_latency_seconds=first_token_latency,
                total_generation_seconds=round(total_duration, 4),
                tokens_generated=tokens_count,
                tokens_per_second=round(tokens_count / max(0.001, total_duration), 2),
                process_ram_mb=ram_used_mb
            )

            self._save_benchmark_results(metrics)
            return metrics

        except Exception as e:
            return ModelBenchmarkMetrics(
                timestamp=time.time(),
                model_name="unknown",
                backend="unknown",
                load_duration_seconds=0.0,
                first_token_latency_seconds=0.0,
                total_generation_seconds=0.0,
                tokens_generated=0,
                tokens_per_second=0.0,
                process_ram_mb=0.0
            )

    def _save_benchmark_results(self, metrics: ModelBenchmarkMetrics) -> None:
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(metrics.model_dump(), f, indent=2)
        except Exception:
            pass


class ModelBenchmark:
    """Static helper alias for ModelBenchmarkUtility."""

    @staticmethod
    def run_benchmark(
        provider: ModelProvider,
        prompt: str = "Hello JARVIS, report your status.",
        output_log_path: Optional[str] = None
    ) -> ModelBenchmarkMetrics:
        util = ModelBenchmarkUtility(cache_file=output_log_path or "data/cache/model-benchmark.json")
        return util.run_benchmark(provider, prompt=prompt, output_log_path=output_log_path)
