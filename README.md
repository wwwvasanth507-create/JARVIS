# MyLLM: Pure CPU GPT-Style Transformer From Scratch

A self-contained, inspectable GPT-style decoder-only Transformer language model built entirely from scratch in Python, targeting **CPU-only execution** on a standard Windows PC.

---

## Mission & Principles

1. **Pure CPU Execution**: Designed and optimized specifically for execution on standard consumer CPUs without requiring GPU, CUDA, ROCm, or specialized accelerator hardware.
2. **Zero External Pretrained Models**: No Hugging Face downloads, no pretrained weights, no pre-packaged tokenizers. Every component—from tokenizer to attention blocks, optimizer, and inference generation—is built from fundamental principles.
3. **Inspectability & Clarity**: Written for clean understanding, modular expansion, and transparent behavior. No hidden abstractions or uninspectable dependencies.
4. **Reproducibility**: Explicit seed management across Python, NumPy, and PyTorch CPU operations.
5. **Modular Architecture**: Clean separation between tokenizer, dataset pipelines, neural architecture, training loops, evaluation metrics, and inference decoders.

---

## Roadmap

| Phase | Description | Status |
| :--- | :--- | :--- |
| **Phase 0** | **Project Foundation**: Architecture blueprint, CPU device utilities, seed control, configuration system, diagnostics, and test suite. | **Completed** |
| **Phase 1** | **Custom Tokenizer**: Byte-Pair Encoding (BPE) / Byte-level tokenizer built from scratch, vocabulary builder, encode/decode pipelines. | **Completed** |
| **Phase 2** | **Model Architecture**: GPT-style decoder-only Transformer (Causal Self-Attention, MLP, LayerNorm/RMSNorm, Embeddings). | **Completed** |
| **Phase 3** | **Data Pipeline**: Text streaming, dataset tokenization, memory-mapped binary files, batch generation. | **Completed** |
| **Phase 4** | **Training Loop**: CPU-tuned AdamW optimizer, learning rate scheduling with warmup & cosine decay, checkpointing. | **Completed** |
| **Phase 5** | **Inference & Evaluation**: Autoregressive decoding (greedy, temperature, top-k, top-p, repetition penalty), KV cache, validation loss, and perplexity. | **Completed** |
| **Phase 6** | **Real Training Workflow**: Production corpus preparation, data leakage validation, CPU scaling profiles, diagnostics telemetry, before/after generation quality, best-checkpoint selection, and documentation. | **Completed** |
| **Phase 7** | **Supervised Instruction-Tuning (SFT)**: Structured instruction format, deterministic serialization templates, response-only loss masking, context length policy, SFT trainer, baseline vs post-tuning evaluation, and telemetry. | **Completed** |
| **Phase 8** | **Conversational Chat Engine**: Multi-turn dialogue management, deterministic chat templates, system prompt support, turn-level context truncation, KV-cached streaming generation, session JSON persistence, and interactive CLI. | **Completed** |
| **Phase 9** | **Local API Server**: Asynchronous FastAPI/Uvicorn HTTP & SSE streaming API, thread-safe session registry, per-session locking, model metadata introspection, explicit persistence, and client test suite. | **Completed** |
| **Phase 10** | **Web UI**: Modern responsive browser chat interface built with React 19, TypeScript, Vite, and Vanilla CSS design system. Real-time SSE streaming, multi-turn dialogue, session persistence, generation settings, model inspection, and pure CPU end-to-end integration. | **Completed** |
| **Phase 11** | **CPU Performance Optimization & Profiling**: Rigorous CPU profiling, PyTorch SDPA attention primitives, tokenizer LRU chunk-caching, preallocated 2D batch generation, inference mode acceleration, benchmark regression suite, and hardware telemetry. | **Completed** |

---

## Repository Structure

```
c:\ll\JARVIS/
├── README.md               # Project documentation and roadmap
├── LICENSE                 # MIT License
├── .gitignore              # Python, PyTorch checkpoints, and cache exclusions
├── requirements.txt        # CPU-only dependencies specification
├── pyproject.toml          # PEP 517/518 build definition & pytest config
├── configs/
│   ├── base.yaml           # Baseline YAML configuration (CPU-first defaults)
│   ├── profiles/           # CPU scaling profiles (tiny_cpu, small_cpu, medium_cpu)
│   └── instruction/        # SFT instruction-tuning profiles (tiny_sft, small_sft)
├── data/
│   ├── raw/                # Unprocessed multi-domain text corpora
│   ├── instructions/       # JSONL instruction datasets (synthetic_sft.jsonl)
│   ├── instruction/        # Binary SFT datasets (train_sft.bin, val_sft.bin, metadata.json)
│   └── tokenized/          # Pre-training binary tokenized sequences, idx, and manifests
├── docs/
│   ├── tokenizer.md        # Deep dive into Byte-Level BPE architecture
│   ├── model.md            # Deep dive into GPT Transformer architecture
│   ├── data.md             # Deep dive into binary dataset pipeline
│   ├── training.md         # Deep dive into CPU training engine & Phase 6 workflow
│   ├── instruction_tuning.md # Deep dive into SFT pipeline & response-only masking
│   ├── chat_engine.md      # Deep dive into conversational chat engine & session state
│   └── api.md              # Deep dive into local ASGI API server, SSE streaming & schemas
├── checkpoints/            # Model weights and training checkpoints
├── logs/                   # Training and runtime execution logs
├── experiments/            # Isolated experiment directories (metrics.jsonl, reports)
├── scripts/
│   ├── check_environment.py # Diagnostic verification script
│   ├── prepare_corpus.py    # Production multi-domain corpus preparation & splitting
│   ├── prepare_instructions.py # Multi-domain synthetic instruction dataset generator
│   ├── inspect_model.py     # Model architecture & memory footprint inspector
│   ├── train_tokenizer.py   # CLI tokenizer training tool
│   ├── build_dataset.py     # CLI binary dataset ingestion & builder tool
│   ├── build_instruction_dataset.py # CLI SFT dataset ingestion & builder tool
│   ├── inspect_dataset.py   # CLI memory-mapped dataset & quality inspector
│   ├── benchmark_data_pipeline.py # End-to-end throughput & integration benchmark
│   ├── train.py             # CLI CPU training engine & experiment runner
│   ├── train_sft.py         # CLI CPU supervised instruction-tuning runner
│   ├── chat.py              # Interactive terminal conversation CLI with streaming
│   ├── benchmark_chat.py    # CPU chat engine latency & throughput benchmark
│   ├── serve.py             # CLI local API server launcher (FastAPI + Uvicorn)
│   ├── test_api.py          # CLI API client smoke test & endpoint validator
│   ├── evaluate.py          # CLI loss and perplexity evaluation
│   ├── generate.py          # CLI autoregressive generation (greedy & sampling)
│   └── inspect_training.py  # CLI checkpoint inspector & state analyzer
├── src/
│   └── myllm/              # Primary Python package
│       ├── __init__.py     # Package exports
│       ├── config.py       # Dataclass & YAML configuration system
│       ├── tokenizer/      # Custom Byte-Level BPE tokenizer
│       │   ├── __init__.py # Public tokenizer exports
│       │   ├── bpe.py      # Pre-tokenization regex & priority merges
│       │   ├── vocabulary.py # Deterministic token ID & byte mappings
│       │   ├── trainer.py  # Deterministic BPE training algorithm
│       │   ├── serialization.py # Safe JSON save/load
│       │   └── tokenizer.py # Unified Tokenizer interface
│       ├── model/          # GPT-style Decoder-Only Transformer
│       │   ├── __init__.py # Public model exports
│       │   ├── attention.py # Causal multi-head self-attention
│       │   ├── mlp.py      # Position-wise GELU feed-forward network
│       │   ├── block.py    # Pre-LayerNorm Transformer block
│       │   ├── gpt.py      # Full GPTModel with tied embeddings
│       │   └── utils.py    # Parameter counter and model summary
│       ├── data/           # Dataset ingestion & binary pipeline
│       │   ├── __init__.py # Public data exports
│       │   ├── corpus.py   # Deterministic corpus streaming & discovery
│       │   ├── text.py     # Safe, conservative text normalization
│       │   ├── tokenizer_pipeline.py # Tokenizer integration & SHA-256 fingerprinting
│       │   ├── metadata.py # Manifest dataclass & JSON serialization
│       │   ├── binary.py   # Streaming uint32 writer & document index
│       │   ├── dataset.py  # Zero-copy memory-mapped TokenDataset reader
│       │   └── batching.py # CPU BatchGenerator yielding (x, y) PyTorch tensors
│       ├── training/       # Optimization and training loops
│       │   ├── __init__.py # Public training subsystem exports
│       │   ├── state.py    # TrainingState dataclass & RNG tracking
│       │   ├── optimizer.py # Parameter-grouped AdamW optimizer
│       │   ├── scheduler.py # Linear warmup & cosine decay LR scheduler
│       │   ├── metrics.py  # Numerical-safe perplexity & throughput tracker
│       │   ├── checkpoint.py # Atomic checkpoint save, load, and pruning
│       │   ├── validation.py # Deterministic evaluation loop
│       │   └── trainer.py  # Core Trainer coordinating loop & clipping
│       ├── chat/           # Conversational chat subsystem
│       │   ├── __init__.py # Public chat exports
│       │   ├── message.py  # ChatMessage and ChatHistory
│       │   ├── template.py # Deterministic ChatTemplate & role safety
│       │   ├── context.py  # ContextManager & turn-level truncation
│       │   ├── telemetry.py # ChatToken, ChatTelemetry, ChatResponse
│       │   ├── session.py  # ChatSession JSON persistence
│       │   └── engine.py   # ChatEngine with KV cache & streaming
│       ├── api/            # Local HTTP & SSE API server subsystem
│       │   ├── __init__.py # Public API exports
│       │   ├── app.py      # FastAPI application factory & routes
│       │   ├── models.py   # Pydantic request/response schemas
│       │   ├── service.py  # APIService coordinating models & concurrency
│       │   ├── sessions.py # Thread-safe SessionRegistry & handles
│       │   ├── errors.py   # Structured API exceptions & handlers
│       │   └── dependencies.py # Dependency injection providers
│       ├── evaluation/     # Loss and perplexity benchmarks
│       ├── inference/      # Autoregressive generation engine
│       └── utils/
│           ├── __init__.py
│           ├── device.py   # CPU resolution & strict guardrails
│           ├── logging.py  # Structured logging
│           └── seed.py     # Deterministic CPU seeding
└── tests/
    ├── __init__.py
    ├── test_config.py      # Configuration tests
    ├── test_device.py      # Strict CPU device selection tests
    ├── test_model.py       # Comprehensive Transformer tests (27 tests)
    ├── test_tokenizer.py   # Comprehensive Byte-Level BPE tests (32 tests)
    ├── test_data.py        # Comprehensive Dataset & Batching tests (24 tests)
    ├── test_training.py    # Comprehensive Training & Optimizer tests (33 tests)
    ├── test_inference.py   # Inference & KV Cache tests (31 tests)
    ├── test_phase6_training.py # Real training workflow tests (8 tests)
    ├── test_phase7_instruction.py # SFT & response-only masking tests (9 tests)
    ├── test_phase8_chat.py # Conversational engine & CLI tests (18 tests)
    ├── test_phase9_api.py  # API server, SSE streaming & sessions (17 tests)
    └── test_utils.py       # Seed and logging tests
```

---

## Installation & Setup

### 1. Prerequisites
- Windows 10/11 with Python 3.10+ (tested on Python 3.14 / 3.12)
- No GPU or CUDA required.

### 2. Install Dependencies
Install the official PyTorch CPU wheel and dependencies:
```powershell
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
pip install -e .
```

---

## Environment Diagnostics

Run the diagnostic script to verify your CPU environment, thread configuration, and strict CPU enforcement:

```powershell
python scripts/check_environment.py
```

Example output:
```
============================================================
           MyLLM System Environment Diagnostics           
============================================================
Python Version           : 3.14.7 (tags/v3.14.7:...)
Platform / OS            : Windows-11-...
PyTorch Version          : 2.14.0+cpu
Configured Device        : cpu
Strict CPU Enforced      : True
Selected Device          : cpu (type: cpu)
CPU Intra-op Threads     : 4
CPU Inter-op Threads     : 4
CUDA Available on System : False
Project Using CUDA       : False
CPU Tensor Test Result   : Shape [2, 2], Device=cpu, Sum=8.0
============================================================
SUCCESS: Environment is verified. Pure CPU execution confirmed.
============================================================
```

---

## Running Unit Tests

Run the test suite via `pytest`:

```powershell
pytest -v
```

All tests confirm:
- `torch.device("cpu")` is strictly selected by default.
- CUDA / GPU requests raise `DeviceNotAllowedError` under strict CPU mode.
- Intra-op CPU threads are configurable.
- Deterministic seeding produces identical random tensor sequences on CPU.
- Configuration loading, overrides, and validation work reliably.
- Byte-level BPE tokenizer satisfies 100% lossless round-trip across Unicode, Tamil, and emojis.

---

## Byte-Level BPE Tokenizer (Phase 1)

### Features
- **100% Python Standard Library**: No Hugging Face, SentencePiece, or tiktoken.
- **Base Vocabulary**: 4 special tokens (`<PAD>`: 0, `<UNK>`: 1, `<BOS>`: 2, `<EOS>`: 3) and 256 individual byte values (`0x00`–`0xFF` mapped to 4–259). Total base size = 260 tokens.
- **Zero <UNK> on Valid UTF-8**: Because all 256 byte values are present, any text can be represented without ever producing `<UNK>`.
- **Lossless Invariant**: `decode(encode(text)) == text` is mathematically guaranteed across English, numbers, punctuation, Tamil, and emojis.
- **Deterministic Tie-Breaking**: When multiple pairs share the same highest frequency, pairs are tie-broken strictly by `(-frequency, pair[0], pair[1])`.
- **Inspectable JSON Format**: No unsafe pickle serialization; stores format version, special tokens, merges, and config.

### Quickstart CLI
Train a tokenizer on your own text files:
```powershell
python scripts/train_tokenizer.py --input data/raw --output checkpoints/tokenizer.json --vocab-size 1000 --min-freq 2
```

### Python API
```python
from myllm.tokenizer import Tokenizer

# Train on custom corpus
tokenizer = Tokenizer.train(["Hello world!", "வணக்கம் தமிழ்நாடு!"], vocab_size=300)

# Encode
ids = tokenizer.encode("Hello world!", add_bos=True, add_eos=True)

# Decode
reconstructed = tokenizer.decode(ids, skip_special_tokens=True)
assert reconstructed == "Hello world!"
```

For complete technical specifications, see [docs/tokenizer.md](file:///c:/ll/JARVIS/docs/tokenizer.md).

---

## GPT-Style Decoder-Only Transformer (Phase 2)

### Features
- **Pure PyTorch CPU Primitives**: Built from scratch without `torch.nn.Transformer` or Hugging Face.
- **Pre-LayerNorm Architecture**: Residual layout ($x = x + \text{Attn}(\text{LN}(x))$, $x = x + \text{MLP}(\text{LN}(x))$) with final LayerNorm.
- **Strict Causal Masking**: Registered lower-triangular buffer guaranteeing tokens attend only to past positions ($j \le i$).
- **Learned Positional Embeddings**: Dedicated embedding table up to `context_length` with explicit boundary validation.
- **Weight Tying**: Input embedding (`wte`) and output projection (`lm_head`) share identical weights, saving parameters and stabilizing representations.
- **Next-Token Prediction Loss**: Built-in shifted cross-entropy loss computation when target labels are provided.
- **CPU Optimization**: 3.25M parameter baseline model executes forward pass in ~6.5 ms on CPU.

### Quickstart Inspection
Run model architecture inspection and measure CPU forward pass latency:
```powershell
python scripts/inspect_model.py
```

### Python API
```python
import torch
from myllm.config import ModelConfig
from myllm.model import GPTModel

# 1. Model configuration
config = ModelConfig(
    vocab_size=1000,
    context_length=128,
    n_layer=4,
    n_head=4,
    n_embd=256,
    weight_tying=True,
)

# 2. Instantiate on CPU
model = GPTModel(config)
model.eval()

# 3. Forward pass
input_ids = torch.tensor([[10, 20, 30, 40]], dtype=torch.long)
logits = model(input_ids)
print("Logits shape:", logits.shape)  # torch.Size([1, 4, 1000])

# 4. Forward with next-token prediction loss
labels = input_ids.clone()
logits, loss = model(input_ids, labels=labels)
print("Loss:", loss.item())
```

For complete technical specifications, see [docs/model.md](file:///c:/ll/JARVIS/docs/model.md).

---

## Data Ingestion & Binary Dataset Pipeline (Phase 3)

### Features
- **Pure CPU Memory-Mapped Binary Storage**: Zero-copy dataset reads via `np.memmap` using compact `uint32` token representations. Scales to multi-gigabyte corpora without loading everything into RAM.
- **Deterministic Lexicographical Ingestion**: Streams single files, directories, or text iterables with strictly sorted discovery across `.txt`, `.md`, and `.text` files.
- **Safe, Non-Destructive Normalization**: Optional BOM stripping (`\ufeff`), universal newline normalization (`\r\n` -> `\n`), and optional Unicode NFC normalization with zero information loss (preserves casing, punctuation, Unicode/Tamil, and emojis).
- **Document Boundary Protection**: Configurable `<BOS>` / `<EOS>` token insertion and document boundary indexing (`.idx` file containing `uint64` document start byte offsets). When `allow_cross_document_sequences=False`, sequences are sampled strictly within individual document boundaries.
- **No Token Leakage Split**: Deterministic, seeded document-level train/validation splitting (e.g. 90/10) preventing cross-split token contamination.
- **SHA-256 Fingerprinting**: Independent SHA-256 fingerprints for both tokenizer artifacts and dataset configurations to detect tokenizer drift or corrupted artifacts.
- **CPU BatchGenerator**: Produces PyTorch `(input_ids, labels)` tensors of shape `[B, T]` with `dtype=torch.long` on `device="cpu"` where labels are shifted by one position ($y = x_{t+1}$). Directly consumable by Phase 2 `GPTModel(input_ids, labels)`.

### Quickstart CLI
Build a binary dataset from text files:
```powershell
python scripts/build_dataset.py --tokenizer checkpoints/tokenizer.json --input data/raw --output data/tokenized --validation-ratio 0.1 --sequence-length 128
```

Inspect a generated dataset manifest and sample tokens:
```powershell
python scripts/inspect_dataset.py --dataset-dir data/tokenized --split train --num-samples 5
```

### Python API
```python
from myllm.config import DataConfig
from myllm.data import TokenDataset, BatchGenerator

# 1. Open memory-mapped dataset
dataset = TokenDataset(
    bin_path="data/tokenized/train.bin",
    sequence_length=128,
    idx_path="data/tokenized/train.idx",
    allow_cross_document_sequences=False,
)

print(f"Total tokens: {dataset.total_tokens:,}")
print(f"Valid sequence windows: {len(dataset):,}")

# 2. Retrieve a single shifted sequence pair (x, y)
x, y = dataset[0]
assert x.shape == (128,)
assert y.shape == (128,)

# 3. Stream CPU training batches
batch_gen = BatchGenerator(
    dataset=dataset,
    batch_size=8,
    sequence_length=128,
    shuffle=True,
    seed=42,
)

for step, (input_ids, labels) in enumerate(batch_gen):
    print(f"Batch {step}: input_ids {input_ids.shape}, labels {labels.shape}, device {input_ids.device}")
    break
```

For complete technical specifications, see [docs/data.md](file:///c:/ll/JARVIS/docs/data.md).

---

## CPU-Only Training Engine (Phase 4)

### Features
- **Pure CPU Execution**: Strictly operates on standard CPU using PyTorch CPU tensors (`torch.long` for tokens, `torch.float32` for parameters and gradients). Disallows CUDA/GPU.
- **Decoupled Weight Decay AdamW**: Automatically partitions model parameters into 2D weight tensors (linear layers, embeddings with decay) and 1D tensors (biases, LayerNorm scale/bias without decay). Handles tied weights safely.
- **Linear-Warmup Cosine-Decay Scheduler**: Warmup from `min_learning_rate` up to peak `learning_rate` over `warmup_steps`, followed by smooth cosine decay down to `min_learning_rate` at `max_steps`.
- **Gradient Clipping & Accumulation**: Enforces maximum gradient norm (`grad_clip_norm`) with finite-value validation, and supports micro-batch gradient accumulation (`gradient_accumulation_steps`).
- **Deterministic Validation & Safe Perplexity**: Zero-gradient evaluation loop under `model.eval()` and `torch.no_grad()`, with overflow-safe perplexity calculation ($PPL = \exp(loss)$ returning `float('inf')` for $loss > 85.0$).
- **Atomic Checkpointing & Pruning**: Safe temporary file writing and atomic renaming (`os.replace`) preventing file corruption. Checkpoints store model state, optimizer momentum, scheduler progression, `TrainingState`, fingerprints, and RNG states. Retains `latest.pt` and `best.pt` while pruning step checkpoints according to `max_checkpoints`.
- **Seamless Resumption**: `--resume checkpoints/latest.pt` smoothly continues training from the saved step and token counter without resetting state.

### Quickstart CLI
Launch a training run on CPU:
```powershell
python scripts/train.py --config configs/base.yaml --train-dataset data/tokenized/train.bin --val-dataset data/tokenized/val.bin --max-steps 100 --batch-size 4
```

Inspect training state and hyperparameters from a checkpoint:
```powershell
python scripts/inspect_training.py --checkpoint checkpoints/latest.pt
```

Resume training from a checkpoint:
```powershell
python scripts/train.py --resume checkpoints/latest.pt --train-dataset data/tokenized/train.bin --max-steps 200
```

### Python API
```python
from myllm.config import AppConfig
from myllm.data import TokenDataset
from myllm.model import GPTModel
from myllm.training import Trainer

# 1. Setup configuration and datasets
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
print(f"Training completed at step {final_state.global_step}, final loss: {final_state.train_loss:.4f}")
```

For complete technical specifications, see [docs/training.md](file:///c:/ll/JARVIS/docs/training.md).

---

## Inference, KV Cache & Evaluation (Phase 5)

> [!NOTE]
> MyLLM at this stage is a research and development language model architecture designed to study Transformers and CPU ML systems engineering. It is not intended to serve as a general-purpose conversational assistant.

### Features
- **Autoregressive Text Generation**: Fully controllable decoding on CPU with greedy argmax, temperature scaling, top-k filtering, nucleus (top-p) sampling, and repetition penalty.
- **Ordered Logit Manipulation Pipeline**: Strictly enforces `raw logits -> repetition penalty -> temperature -> top-k -> top-p -> softmax -> sample/argmax`.
- **Key-Value (KV) Attention Caching**: Layer-by-layer caching of past keys and values ($[B, n\_head, seq\_len, head\_dim]$) eliminating redundant prompt recomputation and achieving $> 1.3\times$ speedup on CPU while maintaining exact numerical logit equivalence ($< 10^{-4}$ max diff).
- **Safe Checkpoint & Tokenizer Validation**: Validates SHA-256 tokenizer fingerprints against saved checkpoint metadata to prevent tokenizer-model mismatches, strictly loads onto CPU, and initializes `model.eval()`.
- **Context Limit Control**: Provides `"error"` and `"truncate_prompt"` strategies to ensure sequence length never exceeds the model context window.
- **Validation Perplexity Evaluation**: Exact token-weighted cross-entropy loss aggregation across arbitrary validation batches under zero-grad CPU execution.
- **Inspectable CLI Utilities**: Full suite of CLI tools for generation (`scripts/generate.py`), evaluation (`scripts/evaluate.py`), and inference benchmarking (`scripts/benchmark_inference.py`).

### CLI Examples

**Autoregressive Generation:**
```powershell
python scripts/generate.py `
  --checkpoint checkpoints/smoke/best.pt `
  --tokenizer checkpoints/smoke/tokenizer.json `
  --prompt "MyLLM is a pure" `
  --max-new-tokens 20 `
  --temperature 0.8 `
  --top-k 40 `
  --top-p 0.9 `
  --repetition-penalty 1.1 `
  --seed 42
```

**Dataset Evaluation & Perplexity:**
```powershell
python scripts/evaluate.py `
  --checkpoint checkpoints/smoke/best.pt `
  --tokenizer checkpoints/smoke/tokenizer.json `
  --dataset data/smoke/val.bin `
  --batch-size 4
```

**CPU Inference & KV Cache Benchmark:**
```powershell
python scripts/benchmark_inference.py `
  --checkpoint checkpoints/smoke/best.pt `
  --tokenizer checkpoints/smoke/tokenizer.json `
  --max-new-tokens 15
```

### Python API Example
```python
from myllm.inference import Generator, GenerationConfig, load_inference_system
from myllm.evaluation import evaluate_perplexity
from myllm.data import TokenDataset

# 1. Load trained model and tokenizer onto CPU
model, tokenizer, metadata = load_inference_system(
    checkpoint_path="checkpoints/smoke/best.pt",
    tokenizer_path="checkpoints/smoke/tokenizer.json",
)

# 2. Configure autoregressive generation
generator = Generator(model=model, tokenizer=tokenizer, device="cpu")
config = GenerationConfig(
    max_new_tokens=30,
    temperature=0.8,
    top_k=40,
    top_p=0.9,
    repetition_penalty=1.1,
    use_cache=True,
    seed=42,
)

# 3. Generate completion
result = generator.generate(prompt="MyLLM is a pure", config=config)
print(f"Generated text: {result.text}")
print(f"Throughput:     {result.tokens_per_second:.2f} tokens/s (CPU)")

# 4. Evaluate perplexity on validation dataset
val_dataset = TokenDataset("data/smoke/val.bin", sequence_length=model.config.context_length)
metrics = evaluate_perplexity(model, val_dataset, batch_size=4)
print(f"Validation Loss: {metrics.mean_loss:.4f} | Perplexity: {metrics.perplexity:.2f}")
```

For complete technical specifications, see [docs/inference.md](file:///c:/ll/JARVIS/docs/inference.md).

---

## Phase 6 — Real Training & Experimentation Workflow

Phase 6 introduces a production-style, reproducible training pipeline on CPU:

```powershell
# 1. Prepare multi-domain corpus with zero cross-split leakage
python scripts/prepare_corpus.py --output-dir data

# 2. Audit dataset quality, sequence windows, and document length distributions
python scripts/inspect_dataset.py --dataset data/tokenized --quality --tokenizer data/tokenized/tokenizer.json

# 3. Inspect CPU model scaling profile & memory footprint estimates
python scripts/inspect_model.py --profile tiny_cpu

# 4. Run reproducible training experiment with telemetry tracking
python scripts/train.py `
  --profile tiny_cpu `
  --train-dataset data/tokenized/train.bin `
  --val-dataset data/tokenized/val.bin `
  --tokenizer data/tokenized/tokenizer.json `
  --experiment-name phase6_real_run `
  --max-steps 50

# 5. Review experiment reports and before vs after text completions
Get-Content experiments/phase6_real_run/training_report.md
Get-Content experiments/phase6_real_run/generations_before.txt
Get-Content experiments/phase6_real_run/generations_after.txt

# 6. Evaluate final best checkpoint
python scripts/evaluate.py `
  --checkpoint experiments/phase6_real_run/checkpoints/best.pt `
  --tokenizer data/tokenized/tokenizer.json `
  --dataset data/tokenized/val.bin
```

For complete technical specifications, see [docs/training.md](file:///c:/ll/JARVIS/docs/training.md).

---

## Phase 7 — Supervised Instruction-Tuning (SFT) Workflow

Phase 7 establishes pure CPU supervised instruction-tuning with response-only loss masking:

```powershell
# 1. Generate diverse synthetic instruction dataset
python scripts/prepare_instructions.py --output data/instructions/synthetic_sft.jsonl

# 2. Build binary SFT dataset with response-only masking & context enforcement
python scripts/build_instruction_dataset.py `
  --input data/instructions/synthetic_sft.jsonl `
  --output-dir data/instruction `
  --tokenizer data/tokenized/tokenizer.json `
  --sequence-length 64

# 3. Inspect SFT dataset, sample sequences, and response-only masking
python scripts/inspect_dataset.py `
  --dataset data/instruction `
  --tokenizer data/tokenized/tokenizer.json

# 4. Execute SFT training from Phase 6 base checkpoint
python scripts/train_sft.py `
  --config configs/instruction/tiny_sft.yaml `
  --experiment-name phase7_sft_run `
  --max-steps 60

# 5. Inspect before vs after SFT completions on identical prompts
Get-Content experiments/phase7/phase7_sft_run/before_sft.json
Get-Content experiments/phase7/phase7_sft_run/after_sft.json
Get-Content experiments/phase7/phase7_sft_run/training_report.md
```

For complete technical specifications, see [docs/instruction_tuning.md](file:///c:/ll/JARVIS/docs/instruction_tuning.md).

---

## Phase 8 — Conversational Chat Engine Workflow

Phase 8 introduces the stateful multi-turn conversational chat engine with streaming responses, KV cache management, turn-level context truncation, and session persistence:

```powershell
# 1. Run interactive terminal chat CLI with real-time streaming
python scripts/chat.py `
  --checkpoint experiments/phase7/phase7_sft_run/checkpoints/best.pt `
  --tokenizer data/tokenized/tokenizer.json `
  --system "You are a concise, helpful assistant."

# Inside the chat session, use interactive commands:
#   /history       - View full message exchange
#   /save <path>   - Save session state to JSON
#   /load <path>   - Restore session from JSON
#   /reset         - Clear history and KV cache
#   /exit          - Exit chat

# 2. Run CPU performance benchmark (latency, throughput, KV cache on vs off)
python scripts/benchmark_chat.py `
  --checkpoint experiments/phase7/phase7_sft_run/checkpoints/best.pt `
  --tokenizer data/tokenized/tokenizer.json `
  --num-runs 3 `
  --max-new-tokens 20

# 3. Run complete regression test suite (194 tests)
python -m pytest
```

For complete technical specifications, see [docs/chat_engine.md](file:///c:/ll/JARVIS/docs/chat_engine.md).

---

## Phase 9 — Local API Server Workflow

Phase 9 establishes the local asynchronous ASGI HTTP API server with Server-Sent Events (SSE) streaming, isolated session management, and explicit persistence:

```powershell
# 1. Launch local API server on CPU (FastAPI + Uvicorn)
python scripts/serve.py `
  --host 127.0.0.1 `
  --port 8000 `
  --checkpoint experiments/phase7/phase7_sft_run/checkpoints/best.pt `
  --tokenizer data/tokenized/tokenizer.json

# 2. View interactive OpenAPI documentation in your browser:
#    http://127.0.0.1:8000/docs
#    http://127.0.0.1:8000/openapi.json

# 3. Run automated client smoke test against running server
python scripts/test_api.py --url http://127.0.0.1:8000

# 4. Run complete regression test suite (211 tests)
python -m pytest
```

For complete technical specifications, see [docs/api.md](file:///c:/ll/JARVIS/docs/api.md).

---

## Phase 10 — Web UI Workflow

Phase 10 introduces the modern browser-based chat interface communicating exclusively with the Phase 9 FastAPI server via HTTP and Server-Sent Events (SSE) streaming:

```
MyLLM
  ↳ Phase 1: Byte-Level BPE Tokenizer
    ↳ Phase 2: GPT-Style Decoder-Only Transformer
      ↳ Phases 3-6: Pre-training & Real Training Engine
        ↳ Phase 7: Supervised Instruction-Tuning (SFT)
          ↳ Phase 8: Conversational Chat Engine (KV-Cached)
            ↳ Phase 9: Local ASGI API Server (FastAPI + SSE)
              ↳ Phase 10: Polished Web UI (React 19 + TypeScript + Vite)
```

```powershell
# 1. Start the API Server (Terminal 1)
python scripts/serve.py --host 127.0.0.1 --port 8000

# 2. Start the Frontend Web UI (Terminal 2)
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173

# 3. Open http://127.0.0.1:5173 in any modern browser

# 4. Run frontend tests (39 tests)
cd frontend
npm test

# 5. Build for production
npm run build
```

For complete technical specifications, see [docs/web_ui.md](file:///c:/ll/JARVIS/docs/web_ui.md).

---

## Phase 11 — CPU Performance Optimization & Engineering

Phase 11 introduces a comprehensive performance benchmarking suite, PyTorch SDPA causal attention primitives, LRU chunk-caching for the Byte-Level BPE tokenizer, zero-copy contiguous 2D batch generation, and full `torch.inference_mode()` acceleration while guaranteeing mathematical equivalence:

### Key Performance Improvements

| Benchmark Domain | Baseline Metric | Optimized Metric | Measured Improvement |
| :--- | :---: | :---: | :---: |
| **Model Forward Latency ($B=1, T=64$)** | 2.47 ms | 1.22 ms | **-50.5% latency (+102% tok/s)** |
| **Model Forward Latency ($B=4, T=64$)** | 4.16 ms | 1.59 ms | **-61.7% latency (+161% tok/s)** |
| **Prompt Prefill Latency** | 2.86 ms | 0.96 ms | **-66.5% latency** |
| **Generation Throughput (Cached)** | 468.1 tok/s | 1,097.3 tok/s | **+134.4% throughput** |
| **Generation Throughput (Inference Mode)**| 543.7 tok/s | 1,050.8 tok/s | **+93.3% throughput** |
| **Tokenizer Encode (Long English)** | 209.0k tok/s | 8,148.0k tok/s | **+3,798% throughput** |
| **Tokenizer Decode (Long English)** | 1,270.5k tok/s | 11,554.8k tok/s | **+809% throughput** |
| **Data Batch Construction ($B=8, T=64$)**| 2,736 batch/s | 20,339 batch/s | **+643% throughput** |
| **Training Step Latency ($B=4, T=64$)** | 17.49 ms | 10.14 ms | **-42.0% latency (+72.5% tok/s)** |
| **FastAPI Synchronous Chat Latency** | 12.44 ms | 4.75 ms | **-61.8% latency** |
| **FastAPI SSE First-Token Latency** | 11.88 ms | 5.56 ms | **-53.2% latency** |

### Running Benchmarks & Regression Guard

```powershell
# 1. Run full CPU benchmark suite
python scripts/benchmark_suite.py --output benchmarks/phase11/current.json

# 2. Compare against baseline with 10% regression threshold
python scripts/compare_benchmarks.py \
    --baseline benchmarks/phase11/baseline.json \
    --current benchmarks/phase11/optimized.json \
    --markdown benchmarks/phase11/comparison.md

# 3. Run complete regression test suite (222 backend tests)
python -m pytest
```

For complete technical specifications, see [docs/performance.md](file:///c:/ll/JARVIS/docs/performance.md).

