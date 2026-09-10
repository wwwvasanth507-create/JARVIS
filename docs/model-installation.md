# Local Model Installation Guide

## Dependencies
The JARVIS local model runtime relies on direct `llama.cpp` Python bindings:
```bash
pip install llama-cpp-python
# or
pip install -e .[llama]
```

## Model Placement
Place compatible GGUF quantized models (e.g. Qwen 2.5 3B / Llama 3.2 1B Q4_K_M) in any of the following directories:
- `models/language/`
- `models/gguf/`
- `models/`

Example file structure:
```text
JARVIS/
└── models/
    └── gguf/
        └── model-Q4_K_M.gguf
```

## Fallback & Graceful Degradation
If no model file is present or `llama-cpp-python` is not installed, JARVIS automatically enters a graceful fallback mode. Deterministic tool operations remain 100% available without application crashes.
