# Model Management & GGUF Discovery Guide

---

## 1. Directory Structure

Local model binaries are placed in `models/`:

```text
models/
├── language/      # Place .gguf language models here (e.g. Qwen2.5-3B-Q4_K_M.gguf)
├── vision/        # Place vision models here (Phase 13)
└── embedding/     # Place embedding models here (Phase 14 & 18)
```

---

## 2. GGUF Model Discovery (`ModelRegistry`)

`ModelRegistry` scans `models/language/` for GGUF files and extracts file attributes:
- `name`: File stem
- `path`: Absolute filesystem path
- `size_mb`: File size in MB
- `quantization`: Auto-detected quantization tier (`Q4_K_M`, `Q5_K_M`, `Q6_K`, `Q8_0`, `Q3_K_M`)

---

## 3. Missing Model Handling

If no GGUF model file is placed in `models/language/`:
1. **JARVIS starts normally without crashing.**
2. When the user requests an AI reasoning task, JARVIS returns:
   > *"No local language model is configured. Please place a compatible local GGUF model in the models/language/ directory and configure it in config/models.yaml."*
3. Non-LLM deterministic commands (Fast Intent Router, application control, screenshots) continue operating cleanly.

---

## 4. RAM Protection & Safety Checks

Before loading any model binary into memory, `ModelProvider` verifies physical RAM headroom:
- Model load is aborted if `free_physical_ram < model_size * 1.2` or `free_ram < 1.5GB`.
- Prevents system swap thrashing or OS out-of-memory crashes.

---

*Model Management Blueprint — Phase 2.*
