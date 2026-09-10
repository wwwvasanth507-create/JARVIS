# Model Troubleshooting & Recovery

## Common Errors & Fixes

### 1. `MODEL_MEMORY_UNAVAILABLE`
- **Cause**: Available system RAM is below `min_free_ram_gb` (1.5 GB) or model file size * 1.2 exceeds free RAM.
- **Fix**: Close resource-heavy applications or select a smaller quantized GGUF model (e.g. Q4_K_M or Q4_0).

### 2. `ModelNotFoundError`
- **Cause**: Configured model file does not exist at `models/gguf/model-Q4_K_M.gguf`.
- **Fix**: Place your GGUF file in `models/gguf/` or `models/language/` and update `config/models.yaml`.

### 3. `BackendUnavailableError`
- **Cause**: `llama-cpp-python` is not installed in the virtual environment.
- **Fix**: Run `pip install llama-cpp-python`.

### 4. `ToolCallParseError`
- **Cause**: LLM output malformed JSON for a tool call.
- **Fix**: `StructuredToolParser` captures the error and returns a clean parse failure message for orchestrator replanning.
