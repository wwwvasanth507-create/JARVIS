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
| **Phase 3** | **Data Pipeline**: Text streaming, dataset tokenization, memory-mapped binary files, batch generation. | Upcoming |
| **Phase 4** | **Training Loop**: CPU-tuned AdamW optimizer, learning rate scheduling with warmup & cosine decay, checkpointing. | Upcoming |
| **Phase 5** | **Inference & Evaluation**: Autoregressive decoding (greedy, top-k, top-p / nucleus sampling, temperature), validation loss, and perplexity. | Upcoming |

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
│   └── base.yaml           # Baseline YAML configuration (CPU-first defaults)
├── data/
│   ├── raw/                # Unprocessed text corpora (.gitkeep)
│   ├── processed/          # Cleaned text datasets (.gitkeep)
│   └── tokenized/          # Binary tokenized sequences (.gitkeep)
├── docs/
│   ├── tokenizer.md        # Deep dive into Byte-Level BPE architecture
│   └── model.md            # Deep dive into GPT Transformer architecture
├── checkpoints/            # Model weights and training checkpoints (.gitkeep)
├── logs/                   # Training and runtime execution logs (.gitkeep)
├── experiments/            # Experiment manifests and metrics (.gitkeep)
├── scripts/
│   ├── check_environment.py # Diagnostic verification script
│   ├── inspect_model.py     # Model architecture & latency inspector
│   └── train_tokenizer.py   # CLI tokenizer training tool
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
│       ├── data/           # Dataset loaders and batch generators
│       ├── training/       # Optimization and training loops
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


