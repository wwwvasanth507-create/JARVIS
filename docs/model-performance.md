# Model Performance & Benchmarking

JARVIS benchmarks local model execution using `ModelBenchmarkUtility` and logs findings to `data/cache/model-benchmark.json`.

## Benchmarking Metrics
- **Load Duration**: Model initialization and RAM mapping time.
- **First Token Latency**: Time to stream the first token chunk.
- **Generation Speed**: Tokens generated per second.
- **Process Memory**: RSS memory consumption during generation.

## Test Results
Running `ModelBenchmarkUtility.run_benchmark(provider)` saves structured metrics to `data/cache/model-benchmark.json`:
```json
{
  "timestamp": 1789048370.22,
  "model_name": "Mock GGUF Model",
  "backend": "mock",
  "load_duration_seconds": 0.0001,
  "first_token_latency_seconds": 0.0001,
  "total_generation_seconds": 0.0002,
  "tokens_generated": 8,
  "tokens_per_second": 8000.0,
  "process_ram_mb": 96.23
}
```
