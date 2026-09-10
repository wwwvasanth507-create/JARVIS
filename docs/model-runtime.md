# Local Model Runtime Subsystem

The Local Model Runtime provides JARVIS with CPU-first local AI inference capabilities without external APIs, cloud services, or Ollama dependencies.

## Architecture

- **`ModelProvider`**: Standardized abstract interface for local language inference (`load()`, `unload()`, `generate()`, `stream()`, `is_available()`, `model_info()`, `health_check()`).
- **`LlamaCppModelProvider`**: Direct `llama.cpp` CPU runtime execution via `llama-cpp-python` (`n_gpu_layers=0`).
- **`MockModelProvider`**: Deterministic mock provider for fast offline unit testing without requiring GGUF model binaries.
- **`ModelRegistry`**: Discovers, inspects, and validates local GGUF models across `models/language/`, `models/gguf/`, and `models/`.
- **`ContextManager`**: Prioritized sliding-window context token budget protection (System > User > Tools > State > Memory > Knowledge > Chat).
- **`StructuredToolParser`**: Extracts and validates JSON tool call structures from model outputs (`{"tool": "...", "arguments": {...}}`).
- **`ModelMemoryChecker`**: Prevents loading models when available system RAM is below requirements (`MODEL_MEMORY_UNAVAILABLE`).
- **`ModelBenchmarkUtility`**: Benchmarks first-token latency, tokens/sec, and memory usage, saving results to `data/cache/model-benchmark.json`.
