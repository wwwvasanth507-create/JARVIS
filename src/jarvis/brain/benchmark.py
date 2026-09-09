"""
CPU Benchmark Infrastructure for JARVIS Local Model Inference.
"""

import json
from pathlib import Path
import time
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from jarvis.brain.provider import ModelProvider, GenerationRequest


class BenchmarkMetrics(BaseModel):
    test_prompt: str
    load_duration_sec: float
    first_token_latency_sec: float
    total_generation_sec: float
    tokens_generated: int
    tokens_per_second: float
    model_name: str
    timestamp: str


class ModelBenchmark:
    """Executes standardized CPU inference benchmarking for JARVIS local models."""

    TEST_PROMPT = "Explain in one sentence what JARVIS is."

    @staticmethod
    def run_benchmark(
        provider: ModelProvider,
        output_log_path: str = "logs/model_benchmark.json",
    ) -> BenchmarkMetrics:
        # Measure load time
        load_start = time.perf_counter()
        provider.initialize()
        load_duration = time.perf_counter() - load_start

        # Measure streaming / first token latency
        req = GenerationRequest(prompt=ModelBenchmark.TEST_PROMPT, max_tokens=64, stream=True)
        gen_start = time.perf_counter()
        first_token_time: Optional[float] = None
        
        token_count = 0
        collected_chunks = []

        try:
            for chunk in provider.stream(req):
                if first_token_time is None:
                    first_token_time = time.perf_counter()
                collected_chunks.append(chunk)
                token_count += 1
        except Exception:
            # Fallback non-streaming measurement if stream is unsupported
            non_stream_resp = provider.generate(GenerationRequest(prompt=ModelBenchmark.TEST_PROMPT, max_tokens=64))
            collected_chunks.append(non_stream_resp.text)
            token_count = non_stream_resp.tokens_generated

        total_gen_duration = time.perf_counter() - gen_start
        first_token_lat = (first_token_time - gen_start) if first_token_time else total_gen_duration

        tps = round(token_count / max(0.001, total_gen_duration), 2)
        info = provider.model_info()

        metrics = BenchmarkMetrics(
            test_prompt=ModelBenchmark.TEST_PROMPT,
            load_duration_sec=round(load_duration, 4),
            first_token_latency_sec=round(first_token_lat, 4),
            total_generation_sec=round(total_gen_duration, 4),
            tokens_generated=token_count,
            tokens_per_second=tps,
            model_name=info.get("name", "Local GGUF Model"),
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
        )

        # Log metrics to file
        log_file = Path(output_log_path)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        with open(log_file, "w", encoding="utf-8") as f:
            f.write(json.dumps(metrics.model_dump(), indent=2))

        return metrics
