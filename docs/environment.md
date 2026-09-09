# Initial System Environment Report

**Date**: September 10, 2026  
**Project**: JARVIS (Local Personal AI Assistant)  
**Status**: Inspected & Verified  

---

## 1. Hardware Specifications

| Component | Measured Value / Model | Technical Details |
| :--- | :--- | :--- |
| **Operating System** | Microsoft Windows 11 Pro | Version `10.0.26200` (64-bit) |
| **Processor (CPU)** | Intel(R) Core(TM) i5-8365U | 4 Cores, 8 Logical Processors @ 1.60 GHz (Turbo up to 4.10 GHz) |
| **System RAM** | 8.00 GB (8,190,248 KB) | ~900 MB Free Physical Memory under baseline workload |
| **Graphics (GPU)** | Intel(R) UHD Graphics 620 | 1 GB Adapter RAM (Integrated Graphics) |
| **NVIDIA CUDA / VRAM** | N/A | Dedicated NVIDIA GPU / `nvidia-smi` not available |
| **Primary Storage (C:)** | ~253.2 GB Total | **163.2 GB Used**, **90.0 GB Free Space** |

---

## 2. Software & Development Tools

| Tool / Runtime | Installed Version | Status |
| :--- | :--- | :--- |
| **Python** | `3.14.7` (64-bit) | Installed (`C:\Users\vasan\AppData\Local\Python\pythoncore-3.14-64\python.exe`) |
| **Package Manager** | `pip 26.2.1` | Installed & verified |
| **Version Control** | `git version 2.55.0.windows.4` | Installed |
| **Shell Environment** | Windows PowerShell 5.1 / PowerShell Core | Operational |

---

## 3. Hardware Resource Constraints & Local Inference Strategy

### Constraints Analysis
1. **RAM Budget (8 GB Total)**:
   - System OS + background apps consume ~6.5–7 GB.
   - Target RAM allocation for JARVIS local LLM inference is **2.0 GB to 3.5 GB max** to avoid system memory swap paging.
2. **Compute Architecture**:
   - Absence of dedicated CUDA VRAM means model inference will execute primarily on CPU using AVX2 instruction set optimizations.
   - Integrated Intel UHD 620 GPU can be evaluated for lightweight OpenCL / SYCL offloading if supported by future backends.

### Local AI Execution Strategy (No Ollama / No Cloud APIs)
- **Quantization Standard**: High-efficiency GGUF 4-bit (Q4_K_M) or 3-bit (Q3_K_M) models (e.g. 1.5B to 3B parameter small language models such as Qwen2.5-1.5B/3B, Llama-3.2-1B/3B, or Phi-3.5-mini).
- **Inference Engine**: Direct native binding via `llama-cpp-python` or compiled C++ `llama.cpp` binaries communicating over stdin/IPC or a local lightweight C++ runner.
- **Memory Footprint Target**:
  - Model weight footprint: ~1.2 GB – 2.2 GB.
  - Context Window: 2,048 – 4,096 tokens (~200–400 MB KV cache).
  - Peak working set memory: ~2.5 GB.

---

## 4. Software Dependencies Plan

No heavy or unnecessary third-party packages will be pre-installed. The incremental installation plan includes:
- `pyyaml` & `pydantic`: For clean config, permission schema validation, and structured tool definitions.
- `llama-cpp-python`: Added in Phase 2 for CPU GGUF model execution.
- `sounddevice` / `piper-tts` / `faster-whisper`: Added in voice phases (Phases 4–6).
- `playwright` / `pyautogui`: Added in automation phases (Phases 7–9).

---

*Report prepared by JARVIS Lead Software Architect.*
