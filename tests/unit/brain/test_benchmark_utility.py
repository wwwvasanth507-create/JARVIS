"""
Unit tests for ModelBenchmarkUtility.
"""

import pytest
import os
import tempfile
from jarvis.brain.benchmark import ModelBenchmarkUtility
from jarvis.brain.provider import MockModelProvider


def test_model_benchmark_utility():
    with tempfile.TemporaryDirectory() as tmp_dir:
        cache_file = os.path.join(tmp_dir, "model-benchmark.json")
        utility = ModelBenchmarkUtility(cache_file=cache_file)
        provider = MockModelProvider()

        results = utility.run_benchmark(provider, prompt="Benchmark test")
        assert "tokens_per_second" in results
        assert results["tokens_generated"] > 0
        assert os.path.exists(cache_file)
