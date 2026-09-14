# Changelog

All notable changes to the MyLLM project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.1.0] - 2026-09-14

### Phase 0 — Project Foundation
- Established clean, modular project blueprint targeting pure CPU-only execution on standard consumer PCs.
- Implemented deterministic seed control across Python, NumPy, and PyTorch CPU routines.
- Built hierarchical dataclass and YAML configuration system (`ModelConfig`, `TrainingConfig`, `DataConfig`, `ServerConfig`, `SystemConfig`).
- Created system environment diagnostic utility (`scripts/check_environment.py`) enforcing strict CPU device selection.

### Phase 1 — Custom Byte-Level BPE Tokenizer
- Implemented custom Byte-Pair Encoding (BPE) tokenizer from fundamental principles without external libraries.
- Built byte-level vocabulary mapping, regex pre-tokenization, and priority merge queue.
- Verified 100% round-trip lossless encoding and decoding across English, code, numbers, symbols, and multilingual Unicode (Tamil).
- Implemented cryptographic SHA-256 tokenizer fingerprinting for dataset compatibility enforcement.

### Phase 2 — GPT-Style Decoder-Only Transformer Architecture
- Built custom GPT Transformer architecture from scratch:
  - Token and learned positional embeddings (`wte`, `wpe`).
  - Weight tying sharing tensor memory between `wte.weight` and `lm_head.weight`.
  - Multi-head causal self-attention with lower-triangular causal masking.
  - Position-wise feed-forward MLP blocks with GELU activation.
  - Pre-LayerNorm residual connections with dropout regularization.
- Verified strict parameter counts, gradient propagation, and numerical sanity.

### Phase 3 — High-Performance Binary Data Pipeline
- Built zero-copy memory-mapped binary dataset pipeline (`train.bin`, `val.bin`, `train.idx`).
- Implemented multi-document handling with continuous sequence sampling and strict document boundary policies.
- Built CPU batch generator producing contiguous int64 tensor pairs `(input_ids, labels)`.
- Added dataset quality validation, cryptographic dataset fingerprinting, and data leakage checks.

### Phase 4 — CPU Training Engine
- Implemented CPU-optimized AdamW optimizer with decoupled weight decay.
- Built learning rate scheduler featuring linear warmup and cosine decay.
- Implemented gradient clipping (`grad_clip_norm`) and gradient accumulation.
- Built stateful checkpointing engine saving model weights, optimizer state, scheduler state, RNG state, and configuration with deterministic resume capability.

### Phase 5 — Autoregressive Inference & Evaluation
- Built autoregressive text generator supporting greedy decoding and stochastic sampling (temperature, top-k, top-p, repetition penalty).
- Implemented Key-Value (KV) cache for fast autoregressive generation avoiding $O(T^2)$ recomputations.
- Verified KV-cached generation produces identical logits ($< 10^{-4}$) and token sequences to naive generation.
- Implemented validation loss and cross-entropy perplexity evaluation metrics.

### Phase 6 — Production Pre-Training Workflow
- Curated multi-domain text corpora (technical documentation, encyclopedic articles, narrative dialogue).
- Profiled CPU scaling across core counts (1, 2, 4, 8 threads) to establish optimal execution baseline.
- Executed full pre-training run with continuous telemetry logging and automated best-checkpoint selection.

### Phase 7 — Supervised Instruction-Tuning (SFT)
- Implemented structured multi-turn conversation format (`<|im_start|>role\ncontent<|im_end|>`).
- Built SFT dataset pipeline with response-only loss masking (zeroing loss over user prompts and system instructions).
- Executed supervised fine-tuning run producing the production `best.pt` checkpoint.
- Verified before/after instruction following quality and telemetry.

### Phase 8 — Conversational Chat Engine
- Implemented stateful `ChatEngine` managing multi-turn dialogue state.
- Added configurable system prompts and turn-level context truncation strategies (`truncate_prompt`, `error`).
- Implemented streaming token generation via generator iterators with KV caching.
- Added session JSON persistence allowing conversations to be saved, reloaded, and resumed.
- Built interactive terminal CLI chat interface (`scripts/chat.py`).

### Phase 9 — Local ASGI API Server
- Built asynchronous REST and Server-Sent Events (SSE) streaming API server using FastAPI and Uvicorn.
- Implemented thread-safe `SessionRegistry` with per-session locking and global CPU inference lock to eliminate thread contention.
- Exposed endpoints for health checks, model introspection, session management, message generation, and explicit persistence.
- Created automated client smoke test (`scripts/test_api.py`) verifying all endpoints.

### Phase 10 — Web UI
- Developed modern, responsive browser interface built with React 19, TypeScript, and Vite.
- Implemented bespoke Vanilla CSS design system with sleek dark mode, glowing accents, and micro-animations.
- Built real-time SSE streaming renderer with live auto-scroll, generation telemetry, and multi-turn session persistence.
- Verified complete browser $\to$ API $\to$ ChatEngine $\to$ SFT model path on pure CPU.
- Passed all 39 frontend unit and live integration tests with 0 Oxlint warnings and 0 TypeScript errors.

### Phase 11 — CPU Performance Optimization & Engineering
- Built comprehensive benchmark suite (`scripts/benchmark_suite.py`) and regression guard (`scripts/compare_benchmarks.py`).
- Integrated PyTorch native `F.scaled_dot_product_attention` for causal attention, delivering 50.5% to 61.7% latency reduction (+102% to +161% tok/s).
- Implemented direct positional embedding slicing and scalar fast-paths for $B=1, T=1$ steps (-66.5% prefill latency).
- Adopted full `torch.inference_mode()` acceleration across inference generation (+93.3% throughput).
- Built LRU chunk-level caching and direct lookup tables for the tokenizer (+3,798% encode throughput, +810% decode throughput).
- Refactored `BatchGenerator` to use preallocated 2D NumPy arrays (+643% batch construction throughput).
- Increased CPU training throughput from 14,634 tok/s to 25,240 tok/s (+72.5%).
- Reduced API synchronous chat latency by 61.8% and SSE first-token latency by 53.2%.
- Retained CPU inference locking and confirmed FP32 as the optimal precision format (rejected BF16 CPU autocast due to 4x slowdown).
- Maintained 100% mathematical equivalence across all 261 regression tests.

### Phase 12 — Packaging, Release & Deployment
- Standardized `pyproject.toml` with runtime dependencies, optional dev dependencies, and programmatically accessible `myllm.version`.
- Separated runtime `requirements.txt` from development `requirements-dev.txt`.
- Hardened API server with `GET /ready` readiness probe and security warning for `0.0.0.0` bindings.
- Created `model_manifest.json` recording cryptographic SHA-256 checksums, fingerprints, and specs for SFT and Smoke models.
- Created standalone model verification CLI (`scripts/verify_model.py`).
- Created single-command local application launcher (`scripts/run_local.py`).
- Created pure CPU Docker containerization files (`Dockerfile`, `.dockerignore`, `docker-compose.yml`).
- Created GitHub Actions CI workflow (`.github/workflows/ci.yml`).
- Verified clean installation in an isolated virtual environment (`.venv_release`).
- Published comprehensive deployment guide (`docs/deployment.md`) and release checklist (`docs/release_checklist.md`).
