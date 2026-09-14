# Byte-Level Byte Pair Encoding (BPE) Tokenizer

This document details the architecture, design, and usage of the custom Byte-Level BPE Tokenizer built from scratch for **MyLLM**.

---

## 1. Overview & Motivation

### What is Byte-Level BPE?
Byte-Level Byte Pair Encoding (BPE) is a subword tokenization technique that operates directly on raw UTF-8 bytes rather than Unicode characters or heuristic whitespace tokens.

### Why Byte-Level Representation?
1. **Zero Out-of-Vocabulary (<UNK>) Issues**: Any valid UTF-8 string is composed of bytes in the range `0x00` through `0xFF` (0–255). By including all 256 byte values in our base vocabulary, **every possible text input is representable**. No text ever crashes the tokenizer, and `<UNK>` is never produced for valid UTF-8 text.
2. **True Multilingual Support**: Unicode characters (such as Tamil `வணக்கம்` or emojis `🚀🤖`) comprise multi-byte UTF-8 sequences. Byte-level BPE naturally treats them as sequences of bytes and learns merges for frequently co-occurring byte sequences without language-specific rules.
3. **No External Dependencies**: Standard tokenizers often rely on large external binaries (SentencePiece, tiktoken, Hugging Face). Our implementation is 100% inspectable Python using only the standard library and NumPy.

---

## 2. Vocabulary Design

The vocabulary uses a deterministic, collision-free ID layout:

| Token ID Range | Category | Description |
| :--- | :--- | :--- |
| `0` | Special Token | `<PAD>` (Padding token) |
| `1` | Special Token | `<UNK>` (Unknown token / fallback) |
| `2` | Special Token | `<BOS>` (Beginning of sequence) |
| `3` | Special Token | `<EOS>` (End of sequence) |
| `4 .. 259` | Base Byte Tokens | 256 raw byte values (`0x00` .. `0xFF`), where byte `b` has token ID `b + 4` |
| `260 .. N` | Learned BPE Merges | Composite tokens created by merging adjacent pairs |

- **Base Vocabulary Size**: Exactly `260` tokens (`4` special + `256` bytes).
- **Total Vocabulary Size**: `260 + len(merges)`.

---

## 3. Lossless Pre-Tokenization

Before applying merges, input text is partitioned losslessly using a regular expression:
```python
r"'s|'t|'re|'ve|'m|'ll|'d| ?\w+| ?[^\s\w]+|\s+(?!\S)|\s+"
```

This ensures that:
- Words with optional leading spaces (e.g., `" world"`) are grouped together, enabling single-token representations of common words with preceding spaces.
- Punctuation and whitespace sequences are isolated without loss.
- Invariant: `"".join(split_text_into_chunks(text)) == text` holds universally for all inputs.

---

## 4. Deterministic BPE Training & Tie-Breaking

### Training Algorithm
1. **Chunk Frequency Aggregation**: Input documents are split into chunks. Each chunk is converted to a tuple of base byte token IDs. A frequency table of chunk tuples is aggregated across the corpus.
2. **Pair Counting**: Adjacent token pairs across all chunk tuples are counted weighted by chunk frequency.
3. **Pair Selection**: The pair with the highest frequency $(\ge \text{min\_pair\_frequency})$ is selected.
4. **Deterministic Tie-Breaking**:
   If multiple candidate pairs have identical frequency, tie-breaking selects the pair with the smallest integer token IDs:
   $$\text{sort key} = (-\text{frequency}, \text{pair}[0], \text{pair}[1])$$
   This guarantees identical results across Python versions, hash seeds, and operating systems.
5. **Vocabulary Update**: The selected pair `(tok_a, tok_b)` is assigned ID `260 + merge_index`.
6. **Corpus Update**: All occurrences of `(tok_a, tok_b)` in the chunk table are replaced with the new ID.
7. **Termination**: Iteration repeats until target `vocab_size` is reached or no pairs meet `min_pair_frequency`.

---

## 5. Encode & Decode Pipeline

### Encoding
```
Text String
  ↓ (Lossless regex partition)
Chunks
  ↓ (UTF-8 encoding + ID offset +4)
Base Byte Token IDs (4–259)
  ↓ (Priority-ordered BPE merges applied per rank)
Merged Token IDs
  ↓ (Optional add_bos / add_eos / truncation)
Final List[int]
```

### Decoding
```
Token IDs: List[int]
  ↓ (Range check 0 <= id < vocab_size; reject invalid IDs with ValueError)
Token Bytes Lookup: id_to_bytes[id] (Special tokens omitted if skip_special_tokens=True)
  ↓
Concatenated Raw Bytes
  ↓ (bytes.decode('utf-8'))
Original Text String
```

### Round-Trip Invariant
For all valid UTF-8 text strings:
$$\text{decode}(\text{encode}(\text{text})) == \text{text}$$

---

## 6. Tokenizer Serialization Format

Tokenizers are saved as human-readable, safe JSON:

```json
{
  "format_version": "1.0",
  "type": "byte_level_bpe",
  "base_vocab_size": 260,
  "vocab_size": 1000,
  "special_tokens": {
    "<PAD>": 0,
    "<UNK>": 1,
    "<BOS>": 2,
    "<EOS>": 3
  },
  "merges": [
    [104, 105],
    [36, 116]
  ],
  "config": {
    "vocab_size": 1000,
    "min_pair_frequency": 2,
    "max_documents": null,
    "max_training_bytes": null
  }
}
```

---

## 7. Command-Line Training (CLI)

Train a tokenizer from a text file or directory of documents:

```powershell
python scripts/train_tokenizer.py --input data/raw/corpus.txt --output checkpoints/tokenizer.json --vocab-size 1000 --min-freq 2
```

Output:
```
=================================================================
           MyLLM Byte-Level BPE Tokenizer Training           
=================================================================
Input Path              : data/raw/corpus.txt
Output Path             : checkpoints/tokenizer.json
Target Vocabulary Size  : 1000
Min Pair Frequency      : 2
Base Vocabulary Size    : 260 (4 special + 256 bytes)
-----------------------------------------------------------------
Documents Ingested      : 125
Bytes Ingested          : 254890 bytes (248.92 KB)
Training merges...
-----------------------------------------------------------------
Documents Processed     : 125
Bytes Processed         : 254890
Initial Vocabulary Size : 260
Final Vocabulary Size   : 1000
Number of Merges Learned: 740
Training Duration       : 0.482 seconds
Output Path             : checkpoints/tokenizer.json
=================================================================
SUCCESS: Tokenizer trained and saved successfully.
=================================================================
```

---

## 8. Python API Usage

```python
from myllm.tokenizer import Tokenizer

# 1. Train on an iterable of strings
corpus = [
    "Hello world! Welcome to MyLLM.",
    "வணக்கம் தமிழ்நாடு! தமிழ் மொழி வாழ்க.",
    "Pure CPU LLM architecture 🚀🤖🔥.",
]
tokenizer = Tokenizer.train(corpus, vocab_size=500, min_pair_frequency=1)

# 2. Encode text
token_ids = tokenizer.encode("Hello world!", add_bos=True, add_eos=True)
print("Token IDs:", token_ids)

# 3. Decode back to text
text = tokenizer.decode(token_ids, skip_special_tokens=True)
print("Decoded  :", text)

# 4. Save and Load
tokenizer.save("checkpoints/tokenizer.json")
reloaded = Tokenizer.load("checkpoints/tokenizer.json")
assert reloaded.encode("Hello world!") == tokenizer.encode("Hello world!")
```
