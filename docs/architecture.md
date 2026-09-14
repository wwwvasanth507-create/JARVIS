# MyLLM: System Architecture & Documentation Index

MyLLM is a self-contained, inspectable GPT-style decoder-only Transformer language model built entirely from scratch in Python, targeting **strict CPU-only execution** on standard personal computers without external deep learning model weights or proprietary engines.

---

## 1. High-Level System Architecture

```
[ Multi-Domain Text Data ]
         ↓
[ Byte-Level BPE Tokenizer ] ─────────────→ [ Tokenizer Model (JSON) ]
         ↓                                               ↓
[ Memory-Mapped Binary Dataset ]                         │
         ↓                                               │
[ GPT Decoder-Only Transformer ]                         │
    ├── Token + Positional Embeddings                    │
    ├── Causal Attention (SDPA)                          │
    ├── Pre-LayerNorm Residuals                          │
    ├── GELU Feed-Forward Blocks                         │
    └── Tied Language Model Head                         │
         ↓                                               │
[ CPU Training & SFT Engine ]                            │
    ├── AdamW Optimizer                                  │
    ├── Cosine Warmup Scheduler                          │
    ├── Response-Only Loss Masking                       │
    └── Best Checkpoint Manager                          │
         ↓                                               │
[ Autoregressive Inference Engine ] ←────────────────────┘
    ├── KV Cache Acceleration
    ├── Sampling & Greedy Decoding
    └── Context Window Policy
         ↓
[ Stateful Conversational ChatEngine ]
    ├── System Prompt Injection
    ├── Turn-Level Context Truncation
    └── Session JSON Serialization
         ↓
[ Local ASGI API Server (FastAPI + SSE) ]
    ├── Liveness / Readiness Probes (/health, /ready)
    ├── REST Session Endpoints
    └── CPU Inference Concurrency Lock
         ↓
[ Web UI (React 19 + TypeScript + Vite) ]
    ├── Real-Time SSE Token Streaming
    ├── Micro-Animation Design System
    └── Session Persistence & Telemetry
```

---

## 2. Subsystem Documentation Directory

Each phase of the MyLLM project is thoroughly documented in dedicated technical guides:

| Subsystem | Document | Key Technical Focus |
| :--- | :--- | :--- |
| **BPE Tokenizer** | [tokenizer.md](file:///c:/ll/JARVIS/docs/tokenizer.md) | Byte-level vocabulary, regex pre-tokenization, merge priority queue, chunk-caching, cryptographic fingerprinting. |
| **Model Architecture** | [model.md](file:///c:/ll/JARVIS/docs/model.md) | GPT decoder-only layers, multi-head causal attention, weight tying, pre-LN blocks, parameter counts. |
| **Binary Data Pipeline** | [data.md](file:///c:/ll/JARVIS/docs/data.md) | Memory-mapped zero-copy token access, contiguous 2D batching, multi-document boundary policies. |
| **CPU Training Engine** | [training.md](file:///c:/ll/JARVIS/docs/training.md) | CPU AdamW optimizer, cosine warmup, gradient accumulation, stateful deterministic checkpointing. |
| **Instruction Tuning** | [instruction_tuning.md](file:///c:/ll/JARVIS/docs/instruction_tuning.md) | Multi-turn prompt formatting, response-only loss masking, context length constraints, SFT evaluation. |
| **Inference & Sampling** | [inference.md](file:///c:/ll/JARVIS/docs/inference.md) | Autoregressive decoding, KV cache mechanics, temperature, top-k/top-p, repetition penalty, perplexity. |
| **Chat Engine** | [chat_engine.md](file:///c:/ll/JARVIS/docs/chat_engine.md) | Turn-level dialogue state, system prompts, KV streaming token generation, JSON session serialization. |
| **Local API Server** | [api.md](file:///c:/ll/JARVIS/docs/api.md) | FastAPI REST & SSE streaming routes, session registry, per-session locking, global CPU inference guard. |
| **Web UI Interface** | [web_ui.md](file:///c:/ll/JARVIS/docs/web_ui.md) | React 19 + TypeScript frontend, Vanilla CSS design tokens, streaming markdown rendering, session switching. |
| **CPU Optimization** | [performance.md](file:///c:/ll/JARVIS/docs/performance.md) | Threading analysis (4 threads optimal), SDPA primitives, `torch.inference_mode()`, benchmarking suite. |
| **Deployment & Ops** | [deployment.md](file:///c:/ll/JARVIS/docs/deployment.md) | Installation workflows, single-command launcher, Docker containerization, health/readiness, security model. |
| **Release Checklist** | [release_checklist.md](file:///c:/ll/JARVIS/docs/release_checklist.md) | Pre-flight release verification, checksum integrity, clean environment tests, CPU policy enforcement. |

---

## 3. Guiding Architectural Invariants

1. **Pure CPU Execution**: Strict CPU execution is enforced throughout. The system never relies on or silently activates CUDA or external acceleration hardware.
2. **Zero External Pretrained Models**: All weights, tokenizers, vocabulary lists, and embeddings are created and trained from scratch.
3. **Inspectability & Determinism**: Every algorithmic decision is transparent, testable, and deterministic when provided a fixed seed.
4. **Local Sovereignty**: All data, sessions, parameters, and models reside on the user's local disk with no network transmission or telemetry collection.
