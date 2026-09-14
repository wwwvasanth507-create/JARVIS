# MyLLM Training Engine & Phase 6 Real Training Workflow

A modular, inspectable, pure **CPU-first training and experimentation subsystem** for the MyLLM GPT decoder-only Transformer.

---

## 1. Overview & Phase 6 Real Training Architecture

The training subsystem trains the `GPTModel` using the `TokenDataset` and `BatchGenerator` pipelines. Every operation runs strictly on CPU using standard PyTorch CPU tensors and automatic differentiation without requiring GPU, CUDA, or ROCm.

### Training Flowchart

```
           Raw Text Corpora (Multi-Domain)
                         ↓
            scripts/prepare_corpus.py
            (Train / Validation Split, Leakage Validation)
                         ↓
           Phase 1 Custom Byte-Level BPE Tokenizer
                         ↓
             Phase 3 Binary Dataset Pipeline
         (train.bin, val.bin, *.idx, metadata.json)
                         ↓
               Dataset Quality & Leakage Audit
                 (DatasetQualityValidator)
                         ↓
            Pre-Training Compatibility Validation
         (validate_training_compatibility: CPU, FP, Vocab, Context)
                         ↓
            TokenDataset (np.memmap, zero RAM copy)
                         ↓
             BatchGenerator (Yields CPU Tensors [B, T])
                         ↓
                      Trainer
                         │
               ┌─────────┴─────────┐
               │  Micro-step Loop  │ (Gradient Accumulation)
               │  Model Forward    │ → logits, cross-entropy loss
               │  loss / accum     │
               │  scaled.backward()│
               └─────────┬─────────┘
                         ↓
               torch.nn.utils.clip_grad_norm_ (Finite checks)
                         ↓
               AdamW Optimizer Step (Decoupled Weight Decay)
                         ↓
               CosineWarmupScheduler Step
                         ↓
               State & Telemetry Update (tok/s, steps/s, loss, PPL)
                         │
               ┌─────────┴─────────┐
               │ Periodic Events   │
               ├───────────────────┤
               │ Telemetry Stream  │ → metrics.jsonl & training.log
               │ Validation Loop   │ → model.eval(), torch.no_grad()
               │ Atomic Checkpoint │ → step_*.pt, latest.pt, best.pt
               └─────────┬─────────┘
                         ↓
              Experiment Post-Processing
              - Best-checkpoint selection (val_loss)
              - Before vs. After prompt generation comparison
              - Overfitting / underfitting diagnostic report
              - training_report.md & summary.json generation
```

---

## 2. Training Corpus Preparation & Quality Validation

### A. Directory Layout
Phase 6 defines a clean, production-style corpus and dataset hierarchy:
```
data/
├── raw/
│   ├── corpus.txt                # Unified multi-domain raw corpus
│   ├── train/
│   │   └── train.txt             # Split train documents
│   └── validation/
│       └── val.txt               # Split validation documents
└── tokenized/
    ├── train.bin                 # Memory-mapped uint32 training token buffer
    ├── val.bin                   # Memory-mapped uint32 validation token buffer
    ├── train.idx                 # Document offset index (uint64)
    ├── val.idx                   # Document offset index (uint64)
    ├── metadata.json             # Dataset manifest with SHA-256 fingerprints
    └── tokenizer.json            # Byte-Level BPE tokenizer model
```

### B. Data Leakage and Quality Validation
Implemented in [src/myllm/data/quality.py](file:///c:/ll/JARVIS/src/myllm/data/quality.py) via `DatasetQualityValidator`.

1. **Document Hashing**: Normalizes and computes SHA-256 digests of document texts (`hash_document_text`).
2. **Cross-Split Data Leakage Prevention**: Identifies if identical documents exist in both train and validation splits. Reports cross-split duplicate count and affected hashes.
3. **Intra-Split Duplicate Detection**: Checks for redundant repetitions within the training split to prevent uncalibrated frequency skew.
4. **Length Distribution Metrics**: Tracks document length in tokens (min, max, mean, median, standard deviation).
5. **CLI Inspection**: Run via `scripts/inspect_dataset.py --dataset data/tokenized --quality --tokenizer data/tokenized/tokenizer.json`.

---

## 3. CPU Model Scaling Profiles & Memory Footprints

Phase 6 defines three realistic scaling profiles in `configs/profiles/` tailored for consumer CPU architectures:

| Profile | Params | Context ($T$) | Layers ($L$) | Heads ($H$) | Dim ($D$) | FP32 Params | AdamW RAM | Activations | Total RAM Budget |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`tiny_cpu`** | ~137 K | 64 | 2 | 2 | 64 | ~535 KB | ~1.04 MB | ~1.88 MB | **~4 MB** |
| **`small_cpu`** | ~843 K | 128 | 4 | 4 | 128 | ~3.22 MB | ~6.43 MB | ~17.0 MB | **~30 MB** |
| **`medium_cpu`**| ~10.8 M | 256 | 6 | 6 | 384 | ~41.4 MB | ~82.8 MB | ~153.0 MB | **~318 MB** |

### Memory Estimation
Implemented in [src/myllm/model/memory.py](file:///c:/ll/JARVIS/src/myllm/model/memory.py):
- **Parameters (FP32)**: $\text{params} \times 4\text{ bytes}$.
- **AdamW State**: $2 \times \text{trainable params} \times 4\text{ bytes}$ (first and second moments $m_t, v_t$).
- **Gradients**: $\text{trainable params} \times 4\text{ bytes}$.
- **Activations**: Layer-by-layer forward activation tensors saved for backpropagation:
  $$\text{Per Block} \approx B \times T \times D \times (11 + 2 \times H \times T) \times 4\text{ bytes}$$
- **Inspect via CLI**:
  ```powershell
  python scripts/inspect_model.py --profile tiny_cpu
  python scripts/inspect_model.py --profile small_cpu
  python scripts/inspect_model.py --profile medium_cpu
  ```

---

## 4. Pre-Training Compatibility Validation

Before starting any training step, [src/myllm/training/compatibility.py](file:///c:/ll/JARVIS/src/myllm/training/compatibility.py) validates:
1. **Device Assertion**: Device must strictly be `"cpu"`. Fails if CUDA or non-CPU device is selected.
2. **Tokenizer Fingerprint Matching**: Ensures the tokenizer model SHA-256 fingerprint matches the dataset metadata fingerprint.
3. **Vocabulary Size Alignment**: Ensures `model.vocab_size >= dataset.tokenizer_vocab_size`.
4. **Context Length Compatibility**: Ensures `model.context_length >= dataset.sequence_length`.
5. **Dataset Internal Consistency**: Ensures `train.bin` byte size equals $\text{train\_tokens} \times 4$ and `val.bin` byte size equals $\text{val\_tokens} \times 4$.

Any mismatch raises a descriptive `CompatibilityError` and halts execution cleanly before any allocation.

---

## 5. Optimization Mechanics & Training Engine

### A. Decoupled Weight Decay (AdamW)
Implemented via `create_optimizer` in [src/myllm/training/optimizer.py](file:///c:/ll/JARVIS/src/myllm/training/optimizer.py):
- **Decayed Group** (`weight_decay = config.weight_decay`): All 2D weight tensors (projections, embeddings).
- **Non-Decayed Group** (`weight_decay = 0.0`): All 1D tensors (biases, LayerNorm gains and biases).
- Tied parameters (`wte.weight` and `lm_head.weight`) are processed once.

### B. Learning Rate Scheduling
Implemented via `CosineWarmupScheduler` in [src/myllm/training/scheduler.py](file:///c:/ll/JARVIS/src/myllm/training/scheduler.py):
- **Linear Warmup Phase** ($0 \le \text{step} < \text{warmup\_steps}$):
  $$\text{lr}(\text{step}) = \text{min\_lr} + (\text{peak\_lr} - \text{min\_lr}) \times \frac{\text{step}}{\text{warmup\_steps}}$$
- **Cosine Decay Phase** ($\text{warmup\_steps} \le \text{step} \le \text{max\_steps}$):
  $$\text{progress} = \frac{\text{step} - \text{warmup\_steps}}{\text{max\_steps} - \text{warmup\_steps}}$$
  $$\text{lr}(\text{step}) = \text{min\_lr} + 0.5 \times (1 + \cos(\pi \times \text{progress})) \times (\text{peak\_lr} - \text{min\_lr})$$

### C. Gradient Clipping & Finite Checks
- `torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=config.grad_clip_norm)`
- Checks for $\text{NaN}$ and $\text{Inf}$ in both forward loss and gradient norms, immediately failing if non-finite numbers occur.

---

## 6. Experiment Telemetry & Overfitting Diagnostics

Implemented in [src/myllm/training/experiment.py](file:///c:/ll/JARVIS/src/myllm/training/experiment.py).

### A. Persistent Artifacts
Every training run creates an isolated directory `experiments/<run_name>/`:
- `config.yaml`: Exact configuration used for the experiment.
- `metrics.jsonl`: Machine-readable streaming JSONL telemetry logged at every step.
- `summary.json`: Final experiment summary metrics, environment specs, and timings.
- `training_report.md`: Markdown report with executive summary, trajectory table, and diagnostics.
- `checkpoints/`: Checkpoint store (`latest.pt`, `best.pt`, `step_*.pt`).
- `generations_before.txt`: Greedy/sampled text completions generated prior to training.
- `generations_after.txt`: Completions on identical prompts using the best checkpoint.

### B. Overfitting / Underfitting Diagnostics
The experiment analyzer computes:
- $\text{Val / Train Ratio} = \frac{\text{final\_val\_loss}}{\text{final\_train\_loss}}$
- **Diagnoses**:
  - `OVERFITTING_WARNING`: If $\text{ratio} > 1.35$ and validation loss is rising while training loss is falling.
  - `UNDERFITTING_WARNING`: If training loss failed to reduce significantly ($> 95\%$ of initial loss).
  - `HEALTHY`: Training and validation losses decrease in tandem without severe divergence.

---

## 7. Deterministic Checkpoint & Resumption

### Mathematical Equivalence
When training is paused at step $N$ and resumed up to step $M$:
- The model weights are reloaded from state dict.
- The AdamW optimizer momentum and variance tensors are restored.
- The CosineWarmupScheduler step counter is restored.
- The PyTorch CPU, Python, and NumPy RNG state seeds are restored.
- The `BatchGenerator` fast-forwards the exact number of consumed batches in the current epoch.

This guarantees bit-for-bit mathematical equivalence between a continuous run ($1 \to M$) and an interrupted/resumed run ($1 \to N \to \text{resume} \to M$). Tested and verified in [tests/test_phase6_training.py](file:///c:/ll/JARVIS/tests/test_phase6_training.py).

---

## 8. CLI Command Quick Reference

### 1. Ingest & Prepare Corpus
```powershell
python scripts/prepare_corpus.py --output-dir data
```

### 2. Inspect Dataset Quality & Leakage
```powershell
python scripts/inspect_dataset.py `
  --dataset data/tokenized `
  --quality `
  --tokenizer data/tokenized/tokenizer.json
```

### 3. Inspect Model Profile Memory
```powershell
python scripts/inspect_model.py --profile tiny_cpu
```

### 4. Execute Real CPU Training Experiment
```powershell
python scripts/train.py `
  --profile tiny_cpu `
  --train-dataset data/tokenized/train.bin `
  --val-dataset data/tokenized/val.bin `
  --tokenizer data/tokenized/tokenizer.json `
  --experiment-name phase6_real_run `
  --max-steps 50
```

### 5. Evaluate Trained Checkpoint
```powershell
python scripts/evaluate.py `
  --checkpoint experiments/phase6_real_run/checkpoints/best.pt `
  --tokenizer data/tokenized/tokenizer.json `
  --dataset data/tokenized/val.bin
```

### 6. Autoregressive Text Generation
```powershell
# Greedy decoding:
python scripts/generate.py `
  --checkpoint experiments/phase6_real_run/checkpoints/best.pt `
  --tokenizer data/tokenized/tokenizer.json `
  --prompt "A Transformer is" `
  --greedy `
  --max-new-tokens 25

# Top-K / Top-P sampling:
python scripts/generate.py `
  --checkpoint experiments/phase6_real_run/checkpoints/best.pt `
  --tokenizer data/tokenized/tokenizer.json `
  --prompt "A Transformer is" `
  --temperature 0.8 `
  --top-k 30 `
  --max-new-tokens 25
```
