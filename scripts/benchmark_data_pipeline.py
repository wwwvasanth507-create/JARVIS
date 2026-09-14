#!/usr/bin/env python3
"""
Performance benchmark and end-to-end integration test for Phase 3 Dataset Pipeline.
Measures docs/sec, bytes/sec, tokens/sec, and memory-mapped retrieval latency on CPU.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Ensure src is in python path
repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root / "src"))

import numpy as np
import torch
from myllm.config import DataConfig, ModelConfig
from myllm.data import BatchGenerator, BinaryDatasetWriter, CorpusReader, TokenDataset, TokenizerPipeline
from myllm.model import GPTModel
from myllm.tokenizer import Tokenizer


def main() -> int:
    print("=" * 65)
    print("       MyLLM Dataset Pipeline Benchmark & Integration (CPU)     ")
    print("=" * 65)

    tmp_dir = repo_root / "data" / "benchmark_cache"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    raw_file = tmp_dir / "bench_raw.txt"

    # 1. Generate multi-paragraph benchmark corpus (English, Tamil, Code, Emojis)
    sample_paragraphs = [
        "The quick brown fox jumps over the lazy dog. Pure CPU execution for language models.",
        "Building a Large Language Model completely from scratch requires modularity.",
        "வணக்கம் உலகம்! தமிழ் ஒரு பழமையான மற்றும் செழுமையான மொழி.",
        "Deep learning architectures rely on multi-head attention and position-wise feed-forward networks.",
        "Rocket launch 🚀 and artificial intelligence 🤖 running on consumer hardware 🔥.",
    ]
    repeated_corpus = "\n\n".join(sample_paragraphs * 200)  # 1000 paragraphs
    raw_file.write_text(repeated_corpus, encoding="utf-8")

    total_bytes = len(repeated_corpus.encode("utf-8"))
    print(f"Benchmark Corpus Size   : {total_bytes:,} bytes ({total_bytes / 1024:.2f} KB)")

    # 2. Train / Load Tokenizer
    tok_file = tmp_dir / "bench_tok.json"
    tokenizer = Tokenizer.train(sample_paragraphs, vocab_size=300, min_pair_frequency=1)
    tokenizer.save(tok_file)
    tok_pipe = TokenizerPipeline(tokenizer)

    # 3. Benchmark Binary Ingestion & Writing
    out_dataset = tmp_dir / "tokenized"
    config = DataConfig(
        output_path=str(out_dataset),
        validation_ratio=0.1,
        sequence_length=64,
        add_eos=True,
        seed=42,
    )
    writer = BinaryDatasetWriter(out_dataset, tok_pipe, config)

    t0 = time.perf_counter()
    metadata = writer.build_from_corpus(CorpusReader(raw_file))
    t_write = time.perf_counter() - t0

    docs_per_sec = metadata.documents_processed / t_write if t_write > 0 else 0
    bytes_per_sec = metadata.bytes_processed / t_write if t_write > 0 else 0
    tokens_per_sec = metadata.total_tokens / t_write if t_write > 0 else 0

    print("-" * 65)
    print(f"Ingestion & Tokenization: {t_write:.4f} seconds")
    print(f"Throughput              : {docs_per_sec:.1f} docs/sec | {bytes_per_sec / (1024*1024):.2f} MB/sec | {tokens_per_sec:,.0f} tokens/sec")
    print(f"Total Tokens Produced   : {metadata.total_tokens:,} (train={metadata.train_tokens:,}, val={metadata.validation_tokens:,})")

    # 4. Benchmark Memory-Mapped Reading
    t1 = time.perf_counter()
    train_dataset = TokenDataset(
        out_dataset / "train.bin",
        sequence_length=64,
        allow_cross_document_sequences=True,
    )
    t_open = time.perf_counter() - t1
    print(f"Memory-Map Open Latency : {t_open * 1000:.3f} ms (zero memory copying)")
    print(f"Total Training Windows  : {len(train_dataset):,}")

    # Read 10,000 sequences from memory map
    t2 = time.perf_counter()
    num_samples = min(5000, len(train_dataset))
    for i in range(num_samples):
        x, y = train_dataset[i]
    t_read = time.perf_counter() - t2
    print(f"Read {num_samples:,} sequences  : {t_read * 1000:.3f} ms ({num_samples / t_read:,.0f} seqs/sec)")

    # 5. Benchmark Batch Generation -> GPTModel Forward Pass
    batch_gen = BatchGenerator(train_dataset, batch_size=8, seed=42)
    input_ids, labels = batch_gen.get_random_batch()

    model_config = ModelConfig(
        vocab_size=len(tokenizer),
        context_length=64,
        n_layer=4,
        n_head=4,
        n_embd=128,
        dropout=0.0,
    )
    model = GPTModel(model_config)
    model.eval()

    t3 = time.perf_counter()
    with torch.no_grad():
        logits, loss = model(input_ids, labels=labels)
    t_forward = time.perf_counter() - t3

    print("-" * 65)
    print("--- End-to-End Integration Check ---")
    print(f"Batch Shape [B, T]      : {list(input_ids.shape)}")
    print(f"Device                  : {input_ids.device} (type: {input_ids.device.type})")
    print(f"Forward Pass Duration   : {t_forward * 1000:.3f} ms")
    print(f"Calculated Loss         : {loss.item():.4f} (finite scalar)")
    print("=" * 65)

    assert logits.device.type == "cpu"
    assert torch.isfinite(loss)
    print("SUCCESS: Dataset pipeline benchmark and model integration confirmed.")
    print("=" * 65)

    # Clean up benchmark temporary files
    import shutil
    shutil.rmtree(tmp_dir, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
