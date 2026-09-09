"""
CPU Inference Benchmark Evaluation Test for JARVIS.
"""

from pathlib import Path
from jarvis.brain.provider import MockModelProvider
from jarvis.brain.benchmark import ModelBenchmark


def test_cpu_model_benchmark_execution(tmp_path):
    log_path = tmp_path / "benchmark_test.json"
    provider = MockModelProvider()

    metrics = ModelBenchmark.run_benchmark(provider, output_log_path=str(log_path))

    assert metrics.tokens_generated > 0
    assert metrics.tokens_per_second > 0.0
    assert metrics.load_duration_sec >= 0.0
    assert log_path.exists()
