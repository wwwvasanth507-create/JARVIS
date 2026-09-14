# MyLLM Inference, KV Cache, and Evaluation Subsystem (Phase 5)

This document details the CPU-first autoregressive generation engine, sampling pipeline, key-value (KV) cache architecture, and evaluation system for MyLLM.

> [!NOTE]
> MyLLM is an educational, inspectable, research-grade language model written from scratch in Python and PyTorch CPU. It does not use Hugging Face Transformers, GPU kernels, or pre-trained external weights.

---

## 1. Architecture Overview

The inference subsystem resides in `src/myllm/inference/` and evaluation utilities reside in `src/myllm/evaluation/`:

```
src/myllm/
├── inference/
│   ├── __init__.py         # Public inference API exports
│   ├── types.py            # GenerationConfig and GenerationResult
│   ├── cache.py            # KVCache layer-by-layer state container
│   ├── sampling.py         # Greedy, temperature, top-k, top-p, repetition penalty
│   ├── stopping.py         # EOS checking and context overflow management
│   ├── loader.py           # Checkpoint loading and tokenizer fingerprint validation
│   ├── generator.py        # Autoregressive generation loop
│   └── benchmark.py        # CPU inference latency and throughput measurement
└── evaluation/
    ├── __init__.py         # Public evaluation API exports
    ├── metrics.py          # EvaluationMetrics dataclass and PPL calculation
    ├── perplexity.py       # Token-weighted cross-entropy loss and perplexity
    ├── evaluator.py        # Multi-prompt generation smoke evaluator
    └── report.py           # Formatting and serialization
```

---

## 2. Checkpoint Loading and Tokenizer Validation

Checkpoints created during training (Phase 4) encapsulate:
- Model weights (`model_state_dict`)
- Architectural dimensions (`config.model`)
- Cryptographic SHA-256 fingerprint of the tokenizer (`tokenizer_fingerprint`)
- Random number generator state (`rng_state`)

### Safe Loading Workflow (`loader.py`)
1. **CPU Device Enforcement**: Model weights are mapped directly to `"cpu"`.
2. **Model Instantiation**: If no external `ModelConfig` is supplied, dimensions are reconstructed directly from checkpoint metadata.
3. **Tokenizer Fingerprint Verification**: The tokenizer passed to `load_checkpoint_for_inference` has its SHA-256 fingerprint computed via `compute_tokenizer_fingerprint(tokenizer)`. If it does not match the checkpoint's recorded fingerprint, a `ValueError` is raised immediately. If the fingerprint is absent, a warning is emitted.
4. **Vocabulary Bounds**: Validates that `len(tokenizer) == model.config.vocab_size`.
5. **Mode**: Puts the model in `model.eval()`.

```python
from myllm.inference.loader import load_inference_system

model, tokenizer, metadata = load_inference_system(
    checkpoint_path="checkpoints/smoke/best.pt",
    tokenizer_path="checkpoints/smoke/tokenizer.json",
)
```

---

## 3. Sampling Pipeline

Logit manipulation strictly follows the ordered pipeline:

$$\text{Raw Logits} \longrightarrow \text{Repetition Penalty} \longrightarrow \text{Temperature} \longrightarrow \text{Top-K} \longrightarrow \text{Top-P (Nucleus)} \longrightarrow \text{Softmax} \longrightarrow \text{Sample / Argmax}$$

### Repetition Penalty
For each token ID $t$ present in the accumulated sequence (prompt + generated tokens):
- If $\text{logit}[t] > 0$: $\text{logit}[t] \leftarrow \frac{\text{logit}[t]}{\text{penalty}}$
- If $\text{logit}[t] \le 0$: $\text{logit}[t] \leftarrow \text{logit}[t] \times \text{penalty}$
- If $\text{penalty} = 1.0$, this step is a no-op.

### Temperature Scaling
$$\text{scaled\_logits} = \frac{\text{logits}}{T}$$
- $T < 1.0$: Sharpens probability distribution (more deterministic).
- $T > 1.0$: Flattens probability distribution (more creative/diverse).
- $T = 1.0$: Standard unscaled distribution.

### Top-K Filtering
Restricts sampling candidates to the top $K$ largest logits. All other positions are set to $-\infty$.
- $K = 0$ or $K \ge V$: Disabled.

### Top-P (Nucleus) Filtering
Sorts candidates in descending probability order and accumulates probability mass until reaching cumulative threshold $p \in (0, 1]$.
- Tokens beyond the threshold are masked with $-\infty$.
- Guarantees that at least the highest-probability token is preserved.
- $p = 1.0$: Disabled.

### Numerical Stability & Safety
- **Finiteness Check**: Before sampling, logits are inspected. If `NaN` or `Inf` are detected, `InferenceError` is raised.
- **Underflow/Overflow Protection**: Top-p shifts logits and computes softmax safely. If all logits are masked, fallback safely selects `argmax`.

---

## 4. Key-Value (KV) Cache

During naive autoregressive generation, generating $N$ tokens requires computing attention over sequences of length $L, L+1, \dots, L+N-1$, yielding $O(N^2)$ attention computation:

$$\text{Time}_{\text{naive}} \propto \sum_{i=1}^{N} (L + i)^2$$

With KV caching, keys ($K$) and values ($V$) from previous positions are retained in memory. Each new step requires computing $Q$ only for the single newly generated token ($T=1$), which attends across the cached past keys and values:

$$\text{Time}_{\text{cached}} \propto \sum_{i=1}^{N} (L + i)$$

### Cache Tensor Shapes
For each Transformer decoder layer $l \in [0, n\_layer - 1]$:
$$\text{Key Tensor: } [B, n\_head, \text{seq\_len}, head\_dim]$$
$$\text{Value Tensor: } [B, n\_head, \text{seq\_len}, head\_dim]$$
where $head\_dim = \frac{n\_embd}{n\_head}$.

### Verification of Mathematical Equivalence
The incremental cached forward pass and the full-sequence forward pass are mathematically equivalent:
$$\max | \text{logits}_{\text{cached}}[i] - \text{logits}_{\text{full}}[i] | < 10^{-4}$$
Under greedy decoding, both naive and cached generation produce identical token sequences.

---

## 5. Stopping Conditions & Context Length Limits

### EOS Termination
When `config.stop_on_eos = True`, generation immediately terminates if the sampled token ID equals `config.eos_token_id` (or the tokenizer's `<|endoftext|>` ID).

### Context Overflow Strategy
If $\text{prompt\_length} + \text{max\_new\_tokens} > \text{context\_length}$:
- `"error"` (default): Raises `ContextOverflowError` with descriptive lengths.
- `"truncate_prompt"`: Left-truncates the prompt, discarding the oldest tokens while preserving the most recent tokens to allow generation within the fixed context window.

---

## 6. Evaluation and Perplexity

Evaluation computes the true token-weighted cross-entropy loss over validation sequences:

$$\mathcal{L} = \frac{\sum_{b=1}^{B} \mathcal{L}_b \cdot N_b}{\sum_{b=1}^{B} N_b}$$

$$\text{Perplexity} = \exp(\mathcal{L})$$

where $N_b$ is the number of valid target tokens (excluding padding / $-100$ targets) in batch $b$.

---

## 7. Command Line Usage

### Generation CLI (`scripts/generate.py`)
```bash
python scripts/generate.py \
    --checkpoint checkpoints/smoke/best.pt \
    --tokenizer checkpoints/smoke/tokenizer.json \
    --prompt "MyLLM is a pure" \
    --max-new-tokens 20 \
    --temperature 0.8 \
    --top-k 40 \
    --top-p 0.9 \
    --repetition-penalty 1.1 \
    --seed 42
```

### Evaluation CLI (`scripts/evaluate.py`)
```bash
python scripts/evaluate.py \
    --checkpoint checkpoints/smoke/best.pt \
    --tokenizer checkpoints/smoke/tokenizer.json \
    --dataset data/smoke/val.bin \
    --batch-size 4
```

### Inference Benchmark CLI (`scripts/benchmark_inference.py`)
```bash
python scripts/benchmark_inference.py \
    --checkpoint checkpoints/smoke/best.pt \
    --tokenizer checkpoints/smoke/tokenizer.json \
    --max-new-tokens 15
```

---

## 8. Verified CPU Performance Benchmark

Benchmark executed on Windows 11 (AMD CPU, 4 intra-op threads, PyTorch CPU 2.14.0):

| Metric | Without KV Cache (Naive) | With KV Cache | Speedup |
| :--- | :---: | :---: | :---: |
| Generation Latency | 0.021 s | 0.016 s | **1.29x** |
| Throughput | 724.98 tok/s | 936.55 tok/s | **1.29x** |
| Output Matching | Exact match | Exact match | Deterministic |
| Prompt Eval Latency | 1.20 ms | 1.20 ms | — |
