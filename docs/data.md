# Data Ingestion, Tokenization Cache, and CPU Dataset Pipeline

This document details the architecture, design, binary storage format, and CLI workflows for the dataset pipeline in **MyLLM**.

---

## 1. Pipeline Overview

The dataset subsystem streams raw text documents, applies safe normalization, tokenizes text with the Phase 1 Byte-Level BPE tokenizer, and serializes token IDs into native `uint32` memory-mappable binary datasets (`train.bin`, `val.bin`) with document boundary indexes (`train.idx`, `val.idx`) and JSON manifests (`metadata.json`).

```
Raw Text Files / Directory
           │
           ▼
  Corpus Ingestion (`CorpusReader`)
  - Deterministic lexicographic file sorting
  - Recursive extension filtering (.txt, .md, .text)
  - Streaming document generation (never loaded all at once)
           │
           ▼
  Text Normalization (`normalize_text`)
  - Strip UTF-8 BOM (\ufeff)
  - Normalize line breaks (\r\n -> \n)
  - Optional Unicode normalization (disabled by default)
  - Strict preservation of case, punctuation, internal whitespace
           │
           ▼
  Tokenizer Pipeline (`TokenizerPipeline`)
  - Phase 1 Byte-Level BPE Tokenizer
  - Deterministic SHA-256 tokenizer fingerprinting
  - Configurable document boundary tokens (add_bos, add_eos)
           │
           ▼
  Binary Dataset Writer (`BinaryDatasetWriter`)
  - Document-level seeded train/val split (prevents token leakage)
  - Incremental uint32 token streaming
  - Document start offsets recorded in uint64 index file (*.idx)
           │
           ├────────────────────────────┐
           ▼                            ▼
  train.bin / val.bin            metadata.json
  train.idx / val.idx            (Manifest, stats, fingerprints)
           │
           ▼
  TokenDataset (`TokenDataset`)
  - Zero-copy np.memmap reading
  - Cross-document vs document-bounded sequence sampling
  - Next-token shifted pairs: x = tokens[i : i+T], y = tokens[i+1 : i+T+1]
           │
           ▼
  Batch Generator (`BatchGenerator`)
  - Yields CPU PyTorch tensors: input_ids [B, T], labels [B, T] in torch.long
           │
           ▼
  GPTModel (Direct compatibility with Phase 2)
```

---

## 2. Text Normalization (`src/myllm/data/text.py`)

Normalization is designed to be **conservative and non-destructive**:
- **BOM Stripping**: Removes leading UTF-8 Byte Order Marks (`\ufeff`) if present.
- **Newline Normalization**: Converts Windows (`\r\n`) and classic Mac (`\r`) newlines to standard Unix `\n`.
- **Unicode Normalization**: Optional (disabled by default to preserve raw character bytes).
- **Non-Destructive Guarantee**: Never lowercases text, never strips punctuation, never collapses internal spaces, and never alters Unicode characters (including Tamil, Indic scripts, and emojis).

---

## 3. Corpus Ingestion (`src/myllm/data/corpus.py`)

- Supports single files, directories of files, or iterables of text strings.
- Directories are scanned recursively (configurable).
- Files are sorted in strict lexicographical order using normalized forward-slash paths, ensuring identical document ordering across Windows, Linux, and macOS.
- Unsupported extensions and binary files are safely excluded.

---

## 4. Document Boundary & EOS Handling

Document boundaries are explicitly demarcated to preserve document context:
- `add_eos = True` (default): appends `EOS_ID` (token ID 3) at the end of each document.
- `add_bos = False` (default): optionally prepends `BOS_ID` (token ID 2).
- `allow_cross_document_sequences`:
  - `False` (default): Training sequences are strictly sampled within document boundaries using `*.idx`.
  - `True`: Sequences are continuously sampled across the entire token stream.

---

## 5. Binary Storage Format & Indexing

- **Data Files (`train.bin`, `val.bin`)**:
  - Contiguous arrays of unsigned 32-bit integers (`np.uint32`).
  - 4 bytes per token.
  - Native little-endian byte ordering.
- **Index Files (`train.idx`, `val.idx`)**:
  - Array of unsigned 64-bit integers (`np.uint64`).
  - Stores the token start offset of each document, plus the total token count as the final entry.
  - Document $k$ spans tokens from `offsets[k]` to `offsets[k+1]`.

---

## 6. Train / Validation Split

- Split ratio is configurable (default: `validation_ratio = 0.1` for a 90/10 split).
- **Document-Level Splitting**: Documents are assigned to either `train` or `val` before tokenization using a seeded pseudo-random number generator (`seed = 42`).
- **Zero Leakage**: Tokens from the same document never appear in both train and validation sets.

---

## 7. Dataset Metadata & Fingerprints (`metadata.json`)

Stored as human-readable JSON:
```json
{
  "format_version": "1.0",
  "dataset_name": "tokenized",
  "tokenizer_fingerprint": "7e81ab3b4e...",
  "tokenizer_vocab_size": 1000,
  "dtype": "uint32",
  "train_tokens": 185420,
  "validation_tokens": 20610,
  "total_tokens": 206030,
  "documents_processed": 500,
  "bytes_processed": 825100,
  "sequence_length": 128,
  "dataset_fingerprint": "3c98f12a7d...",
  "creation_config": {
    "validation_ratio": 0.1,
    "sequence_length": 128,
    "add_bos": false,
    "add_eos": true,
    "allow_cross_document_sequences": false,
    "seed": 42
  },
  "statistics": {
    "average_tokens_per_document": 412.06,
    "min_tokens_per_document": 12,
    "max_tokens_per_document": 3500,
    "unique_tokens_observed": 890,
    "vocab_utilization_percent": 89.0
  }
}
```

---

## 8. CLI Usage

### Build a Dataset
```powershell
python scripts/build_dataset.py --tokenizer checkpoints/tokenizer.json --input data/raw --output data/tokenized --validation-ratio 0.1 --sequence-length 128
```

### Inspect a Dataset (Zero-Copy)
```powershell
python scripts/inspect_dataset.py --dataset data/tokenized --tokenizer checkpoints/tokenizer.json --split train
```

---

## 9. Python API Example

```python
import torch
from myllm.data import BinaryDatasetWriter, CorpusReader, TokenDataset, BatchGenerator, TokenizerPipeline
from myllm.tokenizer import Tokenizer
from myllm.model import GPTModel
from myllm.config import ModelConfig

# 1. Build dataset
tokenizer = Tokenizer.load("checkpoints/tokenizer.json")
pipe = TokenizerPipeline(tokenizer)
writer = BinaryDatasetWriter("data/tokenized", pipe)
metadata = writer.build_from_corpus(CorpusReader("data/raw"))

# 2. Open memory-mapped dataset
dataset = TokenDataset(
    "data/tokenized/train.bin",
    sequence_length=128,
    allow_cross_document_sequences=False,
)

# 3. Create CPU batch generator
batch_gen = BatchGenerator(dataset, batch_size=8, seed=42)
input_ids, labels = batch_gen.get_random_batch()

# 4. Feed directly into Phase 2 GPTModel
model = GPTModel(ModelConfig(vocab_size=len(tokenizer), context_length=128))
model.eval()

logits, loss = model(input_ids, labels=labels)
print(f"Loss: {loss.item():.4f}")
```
