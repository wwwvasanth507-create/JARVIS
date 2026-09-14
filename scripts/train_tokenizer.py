#!/usr/bin/env python3
"""
Command-line interface to train a Byte-Level BPE Tokenizer from scratch for MyLLM.

Usage:
    python scripts/train_tokenizer.py --input data/raw --output checkpoints/tokenizer.json --vocab-size 1000 --min-freq 2
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from typing import Generator, List

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Ensure src is in python path
repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root / "src"))

from myllm.tokenizer import BASE_VOCAB_SIZE, Tokenizer


def iter_documents_from_path(input_path: Path) -> Generator[str, None, None]:
    """Yield text document strings from a file or directory of text files."""
    if input_path.is_file():
        with open(input_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
            if content.strip():
                yield content
    elif input_path.is_dir():
        text_extensions = {".txt", ".md", ".json", ".csv", ".raw"}
        for file_path in sorted(input_path.rglob("*")):
            if file_path.is_file() and file_path.suffix.lower() in text_extensions:
                try:
                    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                        content = f.read()
                        if content.strip():
                            yield content
                except Exception as exc:
                    print(f"Warning: Could not read {file_path}: {exc}", file=sys.stderr)
    else:
        raise FileNotFoundError(f"Input path not found: {input_path}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Train a custom Byte-Level BPE Tokenizer from scratch for MyLLM (CPU-first)."
    )
    parser.add_argument(
        "--input", "-i",
        type=str,
        required=True,
        help="Path to input text file or directory containing text documents.",
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="checkpoints/tokenizer.json",
        help="Path where the trained tokenizer JSON will be saved (default: checkpoints/tokenizer.json).",
    )
    parser.add_argument(
        "--vocab-size", "-v",
        type=int,
        default=1000,
        help="Target total vocabulary size, including 260 base tokens (default: 1000).",
    )
    parser.add_argument(
        "--min-freq", "-f",
        type=int,
        default=2,
        help="Minimum pair frequency to be merged (default: 2).",
    )
    parser.add_argument(
        "--max-docs",
        type=int,
        default=None,
        help="Maximum documents to process (default: all).",
    )
    parser.add_argument(
        "--max-bytes",
        type=int,
        default=None,
        help="Maximum raw text bytes to process (default: all).",
    )

    args = parser.parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)

    if args.vocab_size < BASE_VOCAB_SIZE:
        print(
            f"Error: vocab-size ({args.vocab_size}) must be >= base vocabulary size {BASE_VOCAB_SIZE}.",
            file=sys.stderr,
        )
        return 1

    print("=" * 65)
    print("           MyLLM Byte-Level BPE Tokenizer Training           ")
    print("=" * 65)
    print(f"Input Path              : {input_path}")
    print(f"Output Path             : {output_path}")
    print(f"Target Vocabulary Size  : {args.vocab_size}")
    print(f"Min Pair Frequency      : {args.min_freq}")
    print(f"Base Vocabulary Size    : {BASE_VOCAB_SIZE} (4 special + 256 bytes)")
    print("-" * 65)

    # Collect corpus documents and stats
    start_time = time.perf_counter()
    documents: List[str] = []
    total_bytes = 0

    for doc in iter_documents_from_path(input_path):
        doc_bytes = len(doc.encode("utf-8"))
        if args.max_bytes and (total_bytes + doc_bytes) > args.max_bytes:
            break
        documents.append(doc)
        total_bytes += doc_bytes
        if args.max_docs and len(documents) >= args.max_docs:
            break

    if not documents:
        print(f"Error: No valid text documents found in {input_path}.", file=sys.stderr)
        return 1

    print(f"Documents Ingested      : {len(documents)}")
    print(f"Bytes Ingested          : {total_bytes} bytes ({total_bytes / 1024:.2f} KB)")
    print("Training merges...")

    # Train tokenizer
    tokenizer = Tokenizer.train(
        corpus=documents,
        vocab_size=args.vocab_size,
        min_pair_frequency=args.min_freq,
        max_documents=args.max_docs,
        max_training_bytes=args.max_bytes,
    )

    elapsed_time = time.perf_counter() - start_time
    num_merges = len(tokenizer) - BASE_VOCAB_SIZE

    # Save tokenizer
    saved_path = tokenizer.save(output_path)

    print("-" * 65)
    print(f"Documents Processed     : {len(documents)}")
    print(f"Bytes Processed         : {total_bytes}")
    print(f"Initial Vocabulary Size : {BASE_VOCAB_SIZE}")
    print(f"Final Vocabulary Size   : {len(tokenizer)}")
    print(f"Number of Merges Learned: {num_merges}")
    print(f"Training Duration       : {elapsed_time:.3f} seconds")
    print(f"Output Path             : {saved_path.resolve()}")
    print("=" * 65)
    print("SUCCESS: Tokenizer trained and saved successfully.")
    print("=" * 65)

    return 0


if __name__ == "__main__":
    sys.exit(main())
