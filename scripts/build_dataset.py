#!/usr/bin/env python3
"""
CLI script to build a memory-mapped binary dataset for MyLLM.

Usage:
    python scripts/build_dataset.py --tokenizer checkpoints/tokenizer.json --input data/raw --output data/tokenized --validation-ratio 0.1 --sequence-length 128
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Ensure src is in python path
repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root / "src"))

from myllm.config import DataConfig
from myllm.data import BinaryDatasetWriter, CorpusReader, TokenizerPipeline


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Ingest text corpus and build memory-mapped binary token dataset for MyLLM."
    )
    parser.add_argument(
        "--tokenizer", "-t",
        type=str,
        required=True,
        help="Path to trained tokenizer JSON file.",
    )
    parser.add_argument(
        "--input", "-i",
        type=str,
        required=True,
        help="Path to input text file or directory of text files.",
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="data/tokenized",
        help="Output directory for binary token dataset (default: data/tokenized).",
    )
    parser.add_argument(
        "--validation-ratio", "-v",
        type=float,
        default=0.1,
        help="Fraction of documents assigned to validation set (default: 0.1).",
    )
    parser.add_argument(
        "--sequence-length", "-s",
        type=int,
        default=128,
        help="Context sequence length for training sequences (default: 128).",
    )
    parser.add_argument(
        "--add-bos",
        action="store_true",
        default=False,
        help="Prepend BOS token to each document.",
    )
    parser.add_argument(
        "--no-eos",
        action="store_true",
        default=False,
        help="Do not append EOS token to each document (default: appends EOS).",
    )
    parser.add_argument(
        "--cross-doc",
        action="store_true",
        default=False,
        help="Allow training sequences to span across document boundaries (default: False).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for deterministic train/validation document split (default: 42).",
    )

    args = parser.parse_args()

    tok_path = Path(args.tokenizer)
    input_path = Path(args.input)
    output_dir = Path(args.output)

    if not tok_path.is_file():
        print(f"Error: Tokenizer file not found at {tok_path}", file=sys.stderr)
        return 1

    if not input_path.exists():
        print(f"Error: Input path not found at {input_path}", file=sys.stderr)
        return 1

    print("=" * 65)
    print("            MyLLM Binary Dataset Pipeline (CPU-First)           ")
    print("=" * 65)
    print(f"Tokenizer Path      : {tok_path}")
    print(f"Input Corpus Path   : {input_path}")
    print(f"Output Directory    : {output_dir}")
    print(f"Validation Ratio    : {args.validation_ratio}")
    print(f"Sequence Length     : {args.sequence_length}")
    print(f"Document EOS Token  : {not args.no_eos}")
    print(f"Document BOS Token  : {args.add_bos}")
    print(f"Cross-Doc Sequences : {args.cross_doc}")
    print("-" * 65)

    start_time = time.perf_counter()

    # 1. Initialize Tokenizer Pipeline
    tokenizer_pipe = TokenizerPipeline(tok_path)
    print(f"Tokenizer Loaded    : Vocab Size = {tokenizer_pipe.vocab_size:,}")
    print(f"Tokenizer Fingerprint: {tokenizer_pipe.fingerprint[:16]}...")

    # 2. Setup Corpus Reader
    corpus_reader = CorpusReader(input_path)

    # 3. Setup Dataset Writer
    config = DataConfig(
        input_path=str(input_path),
        output_path=str(output_dir),
        validation_ratio=args.validation_ratio,
        sequence_length=args.sequence_length,
        add_bos=args.add_bos,
        add_eos=not args.no_eos,
        allow_cross_document_sequences=args.cross_doc,
        seed=args.seed,
    )
    writer = BinaryDatasetWriter(
        output_dir=output_dir,
        tokenizer_pipeline=tokenizer_pipe,
        config=config,
    )

    # 4. Stream and write dataset
    print("Processing documents...")
    metadata = writer.build_from_corpus(corpus_reader)
    elapsed_time = time.perf_counter() - start_time

    print("-" * 65)
    print(f"Documents Processed : {metadata.documents_processed:,}")
    print(f"Bytes Ingested      : {metadata.bytes_processed:,}")
    print(f"Total Tokens        : {metadata.total_tokens:,}")
    print(f"  - Train Tokens    : {metadata.train_tokens:,}")
    print(f"  - Val Tokens      : {metadata.validation_tokens:,}")
    print(f"Average Tokens / Doc: {metadata.statistics.get('average_tokens_per_document', 0)}")
    print(f"Vocab Utilization   : {metadata.statistics.get('vocab_utilization_percent', 0)}%")
    print(f"Dataset Fingerprint : {metadata.dataset_fingerprint[:24]}...")
    print(f"Elapsed Time        : {elapsed_time:.3f} seconds")
    print(f"Output Files        : train.bin, val.bin, train.idx, val.idx, metadata.json")
    print("=" * 65)
    print("SUCCESS: Memory-mapped binary dataset built successfully.")
    print("=" * 65)

    return 0


if __name__ == "__main__":
    sys.exit(main())
