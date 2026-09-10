# Local Model Runtime & Inference Architecture Audit

This audit evaluates the existing model inference runtime in JARVIS prior to completing Prompt 013 (Production Local Model Runtime & Real LLM Integration).

## Audit Summary

| Component | Status | Details |
|---|---|---|
| `ModelProvider` Base Interface | **Partially Implemented** | `src/jarvis/brain/provider.py` defines `ModelProvider` ABC, `GenerationRequest`, and `GenerationResponse`. Needs unified `load()`, `health_check()`, and error hierarchy. |
| `MockModelProvider` | **Already Implemented** | Provides deterministic mock generation for offline unit test suites without requiring GGUF files. |
| `LlamaCppModelProvider` | **Partially Implemented** | Direct `llama.cpp` CPU binding using `llama-cpp-python`. Needs RAM safety checks, hardware-aware profiles, and cancellation hooks. |
| `ModelRegistry` & Discovery | **Partially Implemented** | Scans `models/language/`. Needs multi-path discovery (`models/`, `models/gguf/`), file validation, RAM headroom checks, and model selection logic. |
| `ContextManager` | **Partially Implemented** | Trims history by sliding window. Needs strict priority hierarchy (System > User > Tools > State > Memory > Knowledge > Chat). |
| `StructuredToolParser` | **Missing** | Needs JSON tool call extraction (`{"tool": "...", "arguments": {...}}`), schema validation against `ToolRegistry`, and `TOOL_CALL_PARSE_ERROR` handling. |
| Memory Safety Check | **Missing** | Needs pre-load RAM check returning `MODEL_MEMORY_UNAVAILABLE` if model size + headroom exceeds available system RAM. |
| Hardware Profiles | **Partially Implemented** | `config/models.yaml` defines `battery_saver`, `balanced`, `performance`. Needs `ULTRA_LOW`, `LOW`, `MEDIUM`, `HIGH`, `GPU_ACCELERATED` hardware profiles. |
| Health Check & Benchmark | **Partially Implemented** | `src/jarvis/brain/health.py` and `benchmark.py` exist; need structured `ModelHealth` response and `data/cache/model-benchmark.json` output. |

---

## Detailed Findings & Action Plan

1. **Model Provider Interface (`src/jarvis/brain/base.py` & `provider.py`)**:
   - Ensure standard methods: `load()`, `unload()`, `generate()`, `stream()`, `is_available()`, `model_info()`, `health_check()`.
   - Maintain `MockModelProvider` as test/fallback provider.
2. **RAM Safety (`src/jarvis/brain/safety.py`)**:
   - Check available RAM before `llama.cpp` load. Require `model_file_size * 1.2` + 1.5 GB free RAM. Raise `ModelMemoryUnavailableError`.
3. **Structured Tool Call Parser (`src/jarvis/brain/tool_parser.py`)**:
   - Parse tool calls from LLM output, validate against registered `BaseTool` input schema, emit `TOOL_CALL_PARSE_ERROR` on invalid JSON/args.
4. **Context Hierarchy (`src/jarvis/brain/context.py`)**:
   - Enforce explicit context budget prioritization.
5. **Orchestrator Integration (`src/jarvis/core/orchestration/`)**:
   - Route simple deterministic requests via fast-path (`fast_path.py`); route complex AI requests through `ModelProvider`.
6. **Graceful Fallback Mode**:
   - When no GGUF model file is present or `llama-cpp-python` is not installed, JARVIS smoothly falls back to deterministic tool routing without crashing.
