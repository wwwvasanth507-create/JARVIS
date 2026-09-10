# Model Configuration Guide

Configuration options are managed in `config/models.yaml`:

```yaml
models:
  default:
    backend: llama_cpp
    path: models/gguf/model-Q4_K_M.gguf
    context_size: 2048
    temperature: 0.2
    top_p: 0.9
    top_k: 40
    repeat_penalty: 1.1
    n_threads: auto
    n_batch: 512
    n_gpu_layers: 0

hardware_profiles:
  active_profile: "auto" # Options: auto, ULTRA_LOW, LOW, MEDIUM, HIGH, GPU_ACCELERATED

memory_safety:
  min_free_ram_gb: 1.5
  ram_headroom_factor: 1.2
```

## Profiles
- **`ULTRA_LOW`**: 50% CPU cores, 1024 context, `n_gpu_layers: 0`.
- **`LOW` / `MEDIUM`**: 75% CPU cores, 2048 context, `n_gpu_layers: 0`.
- **`HIGH`**: 85% CPU cores, 4096 context, `n_gpu_layers: 0`.
- **`GPU_ACCELERATED`**: 100% CPU cores + GPU layers when available.
