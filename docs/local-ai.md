# Local AI Brain & CPU-First Inference Architecture

---

## 1. Zero Cloud Dependency Principle

**JARVIS** executes local AI reasoning entirely on the user's computer.
- **Zero API Keys**: No OpenAI, Anthropic, or Google AI keys required.
- **No Ollama Requirement**: Built on direct, modular local inference provider abstractions (`ModelProvider` -> `LlamaCppModelProvider`).
- **CPU-First Design**: Default execution targets CPU-only hardware (`gpu_layers = 0`), dynamically scaling thread count without forcing CUDA/GPU acceleration.

---

## 2. Abstraction Architecture

```text
               JARVIS Brain (Agent Loop / Planner)
                               │
                               ▼
                        [ ModelProvider ]
                               │
               ┌───────────────┴───────────────┐
               ▼                               ▼
    [ LlamaCppModelProvider ]        [ MockModelProvider ]
    (Native GGUF CPU Engine)         (Unit Test Engine)
               │                               │
               ▼                               ▼
   Local GGUF Quantized Weights        Deterministic Mock
   (models/language/*.gguf)
```

---

## 3. Hardware-Aware Thread Calculation

To prevent choking system operations (UI, browser, OS tasks), thread count is dynamically calculated:

```python
threads = max(1, physical_cores - 1)
```

### Performance Modes (`config/models.yaml`)
- `battery_saver`: Uses 50% of assigned CPU cores, token limit 1024.
- `balanced`: Uses 75% of assigned CPU cores, token limit 2048.
- `performance`: Uses 100% of assigned CPU cores, token limit 4096.

---

## 4. Token Streaming & Generation Protocol

Generation requests produce token streams directly to the UI layer:
```python
request = GenerationRequest(prompt="Hello JARVIS", stream=True)
for token in provider.stream(request):
    ui.render(token)
```

---

*Local AI Architecture Specification — Phase 2.*
