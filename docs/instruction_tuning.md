# Supervised Instruction-Tuning (SFT) Engine (Phase 7)

A modular, inspectable, pure **CPU-first supervised instruction-tuning (SFT) pipeline** for the MyLLM GPT decoder-only Transformer.

---

## 1. Overview & Architecture

Phase 7 establishes supervised instruction-tuning for MyLLM entirely on CPU. The SFT pipeline takes a pretrained base model checkpoint (from Phase 6), formats structured instruction examples using a deterministic serialization template, applies **response-only loss masking** (`labels[i] = -100` for prompt and padding tokens), and trains the model strictly on generating assistant completions.

```
       Instruction Dataset (JSONL)
        {"instruction": "...", "input": "...", "output": "..."}
                   ↓
      Deterministic Serialization Template
      ### Instruction:\n{instruction}\n\n### Input:\n{input}\n\n### Response:\n
                   ↓
        Phase 1 Custom Byte-Level BPE Tokenizer
                   ↓
      Response-Only Loss Masking Engine
      - Prompt Tokens   : labels[0..P-1] = -100 (Ignored by Cross-Entropy)
      - Response Tokens : labels[P..P+R-1] = Token IDs (Supervised)
      - Appended EOS    : Supervised as final response token
      - Padding Tokens  : labels[P+R..T-1] = -100 (Ignored)
                   ↓
      Binary Memmap-Backed InstructionDataset
      [train_sft.bin, val_sft.bin, metadata.json]
                   ↓
         Base Checkpoint Compatibility Audit
      (validate_sft_compatibility: CPU, Vocab, Dims, Fingerprints)
                   ↓
        SFT Training Engine (Trainer + AdamW)
      - Loss calculated strictly on response tokens
      - Supervised tokens tracked per step
      - Validation response loss and perplexity tracking
                   ↓
        Experiment Telemetry & Verification
      - Before vs. After SFT generation evaluation
      - Best checkpoint selection (lowest validation response loss)
      - training_report.md, metrics.jsonl, summary.json
```

---

## 2. Instruction Data Format & Validation

### A. Schema
Instruction examples are represented in JSONL (JSON Lines) format with three canonical string fields:
```json
{"instruction": "Calculate 12 + 15.", "input": "", "output": "27"}
{"instruction": "Classify the sentiment.", "input": "The model trained quickly and loss dropped.", "output": "Positive"}
```

### B. Validation Rules
Implemented in [src/myllm/data/instruction.py](file:///c:/ll/JARVIS/src/myllm/data/instruction.py) via `InstructionExample`:
- `instruction`: Must be a non-empty, non-whitespace string.
- `output`: Must be a non-empty, non-whitespace string (the expected assistant response).
- `input`: Must be a string (optional supplementary context; defaults to `""`).
- `content_hash()`: Computes deterministic SHA-256 digest of normalized fields for intra-dataset deduplication and cross-split leakage detection.

---

## 3. Instruction Serialization Template

Phase 7 uses a clean, deterministic serialization template compatible with the custom Byte-Level BPE tokenizer.

### Format with Input:
```
### Instruction:
{instruction}

### Input:
{input}

### Response:
{output}
```

### Format without Input:
When `input` is empty, the `### Input:\n` section is omitted:
```
### Instruction:
{instruction}

### Response:
{output}
```

### Prompt Conditioning Prefix:
During inference and prompt tokenization, `format_prompt` ends with `### Response:\n` so the model conditions on this header to generate the completion.

---

## 4. Response-Only Loss Masking

A critical architectural feature of instruction tuning is that **the model is evaluated and updated only on predicting the response**. It must not waste capacity predicting the user's prompt or padding tokens.

### Mathematical Formulation
Given sequence length $T$, prompt length $P$, and response length $R$ ($P + R \le T$):

$$\text{input\_ids} = [t_0, \dots, t_{P-1}, t_P, \dots, t_{P+R-1}, \text{PAD}, \dots, \text{PAD}]$$

$$\text{labels} = [-100, \dots, -100, t_P, \dots, t_{P+R-1}, -100, \dots, -100]$$

In `GPTModel.forward`:
$$\text{shift\_logits} = \text{logits}[:, :-1, :]$$
$$\text{shift\_labels} = \text{labels}[:, 1:]$$
$$\mathcal{L} = \text{CrossEntropy}(\text{shift\_logits}, \text{shift\_labels}, \text{ignore\_index}=-100)$$

Because `ignore_index = -100`:
- For $i < P-1$: $\text{shift\_labels}[i] = \text{labels}[i+1] = -100$ (Loss = 0).
- At position $P-1$ (last prompt token): $\text{shift\_labels}[P-1] = \text{labels}[P] = t_P$ (predicts first response token).
- For $P \le j < P+R-1$: $\text{shift\_labels}[j] = t_{j+1}$ (predicts subsequent response tokens and EOS).
- For padding positions: $\text{shift\_labels} = -100$ (Loss = 0).

**Verified by Mandatory Unit Tests**: Modifying any token or label in the masked prompt positions produces zero difference in cross-entropy loss.

---

## 5. Context Length Policy

When an example exceeds the model context length $T$:
1. **Response Preservation Guarantee**: The response is never silently truncated.
2. **Response-Too-Long Rejection**: If the response tokens (including EOS) require $\ge T$ tokens, the example is rejected with reason `"response_too_long"`.
3. **Prompt Truncation**: If prompt + response exceeds $T$, the prompt is truncated from the left (`prompt_ids = prompt_ids[-(T - len(response_ids)):]`), preserving the response and the immediate `### Response:\n` conditioning prefix.
4. **Padding**: Sequences shorter than $T$ are padded with `<PAD>` (token ID 0), with labels set to `-100`.

---

## 6. Train / Validation Split & Leakage Audit

- **Document-Level Split**: Examples are split deterministically using salted SHA-256 hashes (`seed = 42`, default 85% train / 15% val).
- **Leakage Prevention**: Validates that the intersection of training content hashes and validation content hashes is empty ($0\%$ cross-split leakage).
- **Deduplication**: Identifies and reports any duplicate instruction examples.

---

## 7. SFT Configuration & CPU Profiles

Phase 7 introduces profiles in `configs/instruction/`:
- **`tiny_sft.yaml`**: Context length 64, batch size 4, lr 3e-4, 60 steps on CPU (~4 MB RAM).
- **`small_sft.yaml`**: Context length 128, batch size 4, lr 2e-4, 100 steps on CPU (~30 MB RAM).

Configuration specifies:
```yaml
instruction:
  base_checkpoint: "experiments/phase6_real_run/checkpoints/best.pt"
  template_version: "1.0"
  mask_prompt_labels: true
  supervise_eos: true
  response_truncation_policy: "reject"
  instruction_data_path: "data/instruction"
```

---

## 8. CLI Command Quickstart

### 1. Generate Synthetic Multi-Domain Instructions
```powershell
python scripts/prepare_instructions.py --output data/instructions/synthetic_sft.jsonl
```

### 2. Build Binary SFT Dataset
```powershell
python scripts/build_instruction_dataset.py `
  --input data/instructions/synthetic_sft.jsonl `
  --output-dir data/instruction `
  --tokenizer data/tokenized/tokenizer.json `
  --sequence-length 64
```

### 3. Inspect SFT Dataset & Response Masking
```powershell
python scripts/inspect_dataset.py `
  --dataset data/instruction `
  --tokenizer data/tokenized/tokenizer.json
```

### 4. Run SFT Training with Baseline vs Post-Tuning Evaluation
```powershell
python scripts/train_sft.py `
  --config configs/instruction/tiny_sft.yaml `
  --experiment-name phase7_sft_run `
  --max-steps 60
```

### 5. Review Generated Evaluation Artifacts
```powershell
# Before-tuning baseline generations:
Get-Content experiments/phase7/phase7_sft_run/before_sft.json

# After-tuning generations on identical prompts:
Get-Content experiments/phase7/phase7_sft_run/after_sft.json

# Comprehensive Markdown report:
Get-Content experiments/phase7/phase7_sft_run/training_report.md
```

---

## 9. Synthetic Dataset Disclaimer & Known Limitations

> [!NOTE]
> **Synthetic Dataset Disclaimer**: The provided `synthetic_sft.jsonl` dataset is explicitly designed for pipeline validation, response-only loss masking verification, and deterministic workflow testing. It is not intended to produce generalized broad-domain conversational intelligence.
>
> **Known Limitations**:
> 1. With small models (~137K parameters) and modest instruction counts, greedy decoding may produce repetitive patterns when prompts significantly diverge from the training distribution.
> 2. CPU execution time bounds context windows to $T \le 256$ for interactive turnaround times.
