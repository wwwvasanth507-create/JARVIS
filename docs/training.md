# MyLLM Training Engine (Phase 4)

A modular, inspectable, pure **CPU-first training subsystem** for the MyLLM GPT decoder-only Transformer.

---

## 1. Overview & Architecture

The training subsystem trains the Phase 2 `GPTModel` using the Phase 3 `TokenDataset` and `BatchGenerator`. Every operation runs strictly on CPU using standard PyTorch CPU tensors and automatic differentiation.

### Training Flowchart

```
           Raw Text Corpora
                  ↓
          Phase 1 Tokenizer (Byte-Level BPE)
                  ↓
       Phase 3 Binary Dataset Pipeline
       (train.bin, val.bin, *.idx, metadata.json)
                  ↓
         TokenDataset (np.memmap, zero RAM copy)
                  ↓
       BatchGenerator (Yields CPU Tensors [B, T])
                  ↓
               Trainer
                  │
        ┌─────────┴─────────┐
        │  Micro-step Loop  │ (Gradient Accumulation)
        │  Model Forward    │ → logits, loss
        │  loss / accum     │
        │  scaled.backward()│
        └─────────┬─────────┘
                  ↓
        torch.nn.utils.clip_grad_norm_
                  ↓
        AdamW Optimizer Step (Decoupled Weight Decay)
                  ↓
        CosineWarmupScheduler Step
                  ↓
        State & Metrics Update (tok/s, steps/s, loss, PPL)
                  │
        ┌─────────┴─────────┐
        │ Periodic Events   │
        ├───────────────────┤
        │ Periodic Log      │ → Console & training.log
        │ Validation Loop   │ → model.eval(), torch.no_grad()
        │ Atomic Checkpoint │ → step_*.pt, latest.pt, best.pt
        └───────────────────┘
```

---

## 2. Optimization Mechanics

### A. Decoupled Weight Decay (AdamW)
Implemented via `create_optimizer` in [src/myllm/training/optimizer.py](file:///c:/ll/JARVIS/src/myllm/training/optimizer.py).

Parameters are partitioned into two disjoint groups:
1. **Decayed Group** (`weight_decay = config.weight_decay`):
   - All 2D and higher-dimensional weight tensors:
     - Linear projection weights (`c_attn.weight`, `c_proj.weight`, `c_fc.weight`).
     - Embedding tables (`wte.weight`, `wpe.weight`).
2. **Non-Decayed Group** (`weight_decay = 0.0`):
   - All 1D tensors:
     - Biases (`c_attn.bias`, `c_proj.bias`, `c_fc.bias`).
     - LayerNorm parameters (`ln_1.weight`, `ln_1.bias`, `ln_2.weight`, `ln_2.bias`, `ln_f.weight`, `ln_f.bias`).

Weight tying is respected: tied parameters (`wte.weight` and `lm_head.weight`) are processed once, avoiding duplicated weight decay or gradients.

### B. Learning Rate Scheduling
Implemented via `CosineWarmupScheduler` in [src/myllm/training/scheduler.py](file:///c:/ll/JARVIS/src/myllm/training/scheduler.py):
- **Linear Warmup Phase** ($0 \le \text{step} < \text{warmup\_steps}$):
  $$\text{lr}(\text{step}) = \text{min\_lr} + (\text{peak\_lr} - \text{min\_lr}) \times \frac{\text{step}}{\text{warmup\_steps}}$$
- **Cosine Decay Phase** ($\text{warmup\_steps} \le \text{step} \le \text{max\_steps}$):
  $$\text{progress} = \frac{\text{step} - \text{warmup\_steps}}{\text{max\_steps} - \text{warmup\_steps}}$$
  $$\text{lr}(\text{step}) = \text{min\_lr} + 0.5 \times (1 + \cos(\pi \times \text{progress})) \times (\text{peak\_lr} - \text{min\_lr})$$
- **Post-Decay Phase** ($\text{step} > \text{max\_steps}$):
  $$\text{lr}(\text{step}) = \text{min\_lr}$$

### C. Gradient Clipping
Gradient clipping prevents exploding gradients:
- `torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=config.grad_clip_norm)`
- Pre-clipping gradient norms are checked for finite values. If $\text{NaN}$ or $\text{Inf}$ is encountered, a `TrainingError` is raised immediately to halt corrupt training.

### D. Gradient Accumulation
Simulates larger effective batch sizes without increasing memory:
- $\text{Effective Batch Size} = \text{batch\_size} \times \text{gradient\_accumulation\_steps}$
- Gradients are accumulated across micro-batches:
  $$\text{loss}_{\text{scaled}} = \frac{\text{loss}}{\text{gradient\_accumulation\_steps}}$$
- Gradients are cleared via `optimizer.zero_grad(set_to_none=True)` only after the accumulation steps complete.

---

## 3. Validation & Perplexity

### A. Deterministic Evaluation Loop
Implemented in [src/myllm/training/validation.py](file:///c:/ll/JARVIS/src/myllm/training/validation.py):
- Runs under `model.eval()` and `torch.no_grad()`.
- Uses fixed validation seeds for reproducibility.
- Guarantees restoring the model's prior training state (`model.train(prev_mode)`).
- Never modifies optimizer states or scheduler counters.

### B. Numerically Safe Perplexity
Implemented in [src/myllm/training/metrics.py](file:///c:/ll/JARVIS/src/myllm/training/metrics.py):
- Formula: $\text{PPL} = \exp(\text{Loss})$.
- Overflow protection: If $\text{Loss} > 85.0$, returns `float("inf")` instead of generating $\text{NaN}$ or crashing with `OverflowError`.
- Validates that cross-entropy loss is non-negative.

---

## 4. Checkpointing & Resumption

### A. Atomic File Writing
Implemented in [src/myllm/training/checkpoint.py](file:///c:/ll/JARVIS/src/myllm/training/checkpoint.py):
1. Payload is serialized to a temporary file: `.tmp_<uuid>_step_00000050.pt`.
2. OS flush is performed.
3. Atomic rename via `os.replace` guarantees zero file corruption if execution is interrupted mid-write.

### B. Checkpoint Contents
Each `.pt` file contains:
- `format_version`: `"1.0.0"`
- `saved_at`: UTC timestamp string
- `model_state_dict`: Model weights
- `optimizer_state_dict`: AdamW momentum buffers and second-moment estimators
- `scheduler_state`: Step index and learning rate progression
- `training_state`: Global step, micro step, tokens seen, losses, best metrics
- `config`: Complete nested YAML configuration dictionary
- `tokenizer_fingerprint`: SHA-256 fingerprint of tokenizer
- `dataset_fingerprint`: SHA-256 fingerprint of dataset
- `model_metadata`: Total, trainable, and tied parameter counts
- `rng_state`: Python, NumPy, and PyTorch CPU RNG states

### C. Automated Pruning
The checkpoint manager automatically deletes older step checkpoints exceeding `max_checkpoints`, while perpetually preserving:
- `latest.pt`: The most recent successful checkpoint.
- `best.pt`: The checkpoint with the lowest validation loss.

### D. Resuming Training
To resume training:
```powershell
python scripts/train.py --resume checkpoints/latest.pt --train-dataset data/tokenized/train.bin --max-steps 500
```
- Restores weights, optimizer moments, scheduler step, and RNG states.
- Training resumes from `global_step` without resetting counters to 0.

---

## 5. CLI Usage

### Launch Training
```powershell
python scripts/train.py `
  --config configs/base.yaml `
  --train-dataset data/tokenized/train.bin `
  --val-dataset data/tokenized/val.bin `
  --tokenizer checkpoints/tokenizer.json `
  --checkpoint-dir checkpoints `
  --max-steps 100 `
  --batch-size 4 `
  --learning-rate 0.0003
```

### Inspect Checkpoint
```powershell
python scripts/inspect_training.py --checkpoint checkpoints/latest.pt
```

Example Output:
```
=================================================================
                 MyLLM Checkpoint Inspector                     
=================================================================
File Path               : C:\ll\JARVIS\checkpoints\latest.pt
File Size               : 37.51 MB
Format Version          : 1.0.0
Creation Timestamp      : 2026-09-14T09:22:53.977983+00:00
-----------------------------------------------------------------
--- Model Architecture & Parameters ---
Total Parameters        : 3,269,120
Trainable Parameters    : 3,269,120
Layers (n_layer)        : 4
Attention Heads (n_head): 4
Embedding Dim (n_embd)  : 256
Context Length          : 128
Vocab Size              : 300
-----------------------------------------------------------------
--- Training State Progress ---
Global Optimizer Step   : 20
Tokens Processed        : 10,240
Latest Learning Rate    : 3.00e-05
Latest Train Loss       : 2.9101
=================================================================
```

---

## 6. Python API Quickstart

```python
from myllm.config import AppConfig
from myllm.data import TokenDataset
from myllm.model import GPTModel
from myllm.training import Trainer

# 1. Setup config and datasets
app_config = AppConfig()
train_dataset = TokenDataset("data/tokenized/train.bin", sequence_length=128)
val_dataset = TokenDataset("data/tokenized/val.bin", sequence_length=128)

# 2. Instantiate Model and Trainer
model = GPTModel(app_config.model)
trainer = Trainer(
    model=model,
    train_dataset=train_dataset,
    val_dataset=val_dataset,
    config=app_config,
)

# 3. Execute training loop
final_state = trainer.train()
print(f"Training completed at step {final_state.global_step}, loss: {final_state.train_loss:.4f}")
```
