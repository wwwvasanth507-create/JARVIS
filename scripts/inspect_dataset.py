#!/usr/bin/env python3
"""
CLI script to inspect a tokenized binary dataset for MyLLM without loading the entire dataset into RAM.

Usage:
    python scripts/inspect_dataset.py --dataset data/tokenized --tokenizer checkpoints/tokenizer.json
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Ensure src is in python path
repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root / "src"))

from myllm.data import DatasetMetadata, TokenDataset
from myllm.tokenizer import Tokenizer


def format_file_size(num_bytes: int) -> str:
    """Format bytes as human readable string."""
    for unit in ["B", "KB", "MB", "GB"]:
        if abs(num_bytes) < 1024.0:
            return f"{num_bytes:.2f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.2f} TB"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspect metadata, sizes, and sample sequences of a built binary dataset without loading into RAM."
    )
    parser.add_argument(
        "--dataset", "-d",
        type=str,
        required=True,
        help="Path to directory containing tokenized dataset (metadata.json, train.bin, etc.).",
    )
    parser.add_argument(
        "--tokenizer", "-t",
        type=str,
        default=None,
        help="Optional path to tokenizer.json to decode sample tokens into human-readable text.",
    )
    parser.add_argument(
        "--split", "-s",
        type=str,
        default="train",
        choices=["train", "val"],
        help="Split to sample sequences from ('train' or 'val', default: 'train').",
    )

    args = parser.parse_args()
    dataset_dir = Path(args.dataset)
    meta_path = dataset_dir / "metadata.json"

    if not meta_path.is_file():
        print(f"Error: metadata.json not found in {dataset_dir}", file=sys.stderr)
        return 1

    metadata = DatasetMetadata.load(meta_path)

    # Optional tokenizer for decoding sample
    tokenizer = None
    if args.tokenizer:
        tok_path = Path(args.tokenizer)
        if tok_path.is_file():
            tokenizer = Tokenizer.load(tok_path)

    print("=" * 65)
    print("             MyLLM Binary Dataset Inspection Manifest             ")
    print("=" * 65)
    print(f"Dataset Directory        : {dataset_dir.resolve()}")
    print(f"Dataset Name             : {metadata.dataset_name}")
    print(f"Format Version           : {metadata.format_version}")
    print(f"Token Storage Dtype      : {metadata.dtype}")
    print(f"Sequence Length          : {metadata.sequence_length}")
    print(f"Total Tokens             : {metadata.total_tokens:,}")
    print(f"  - Train Tokens         : {metadata.train_tokens:,}")
    print(f"  - Validation Tokens    : {metadata.validation_tokens:,}")
    print(f"Documents Ingested       : {metadata.documents_processed:,}")
    print(f"Raw Bytes Ingested       : {metadata.bytes_processed:,} ({format_file_size(metadata.bytes_processed)})")
    print(f"Tokenizer Fingerprint    : {metadata.tokenizer_fingerprint[:24]}...")
    print(f"Dataset Fingerprint      : {metadata.dataset_fingerprint[:24]}...")
    print("-" * 65)

    # File size inspection on disk
    print("Files on Disk:")
    for fname in ["train.bin", "val.bin", "train.idx", "val.idx", "metadata.json"]:
        fpath = dataset_dir / fname
        if fpath.is_file():
            size_str = format_file_size(fpath.stat().st_size)
            print(f"  - {fname:<15} : {size_str:>10} ({fpath.stat().st_size:,} bytes)")
        else:
            print(f"  - {fname:<15} : [Not Found]")

    print("-" * 65)
    print("Dataset Statistics:")
    for k, v in metadata.statistics.items():
        print(f"  - {k:<30} : {v}")

    # Inspect sample sequences using memory mapping
    split_bin = dataset_dir / f"{args.split}.bin"
    if split_bin.is_file() and split_bin.stat().st_size > 0:
        try:
            dataset = TokenDataset(
                bin_path=split_bin,
                sequence_length=min(metadata.sequence_length, 32),  # preview 32 tokens
                allow_cross_document_sequences=True,
            )
            if len(dataset) > 0:
                x_sample, y_sample = dataset[0]
                print("-" * 65)
                print(f"Sample First Sequence ({args.split}.bin, first {len(x_sample)} tokens):")
                print(f"  x (input tokens)  : {list(x_sample[:16])}...")
                print(f"  y (shifted target): {list(y_sample[:16])}...")

                if tokenizer is not None:
                    decoded_text = tokenizer.decode(x_sample, skip_special_tokens=False)
                    print(f"  Decoded x Text    : {decoded_text!r}")
        except Exception as exc:
            print(f"Note on sequence preview: {exc}")

    print("=" * 65)
    print("SUCCESS: Memory-mapped dataset inspection complete.")
    print("=" * 65)
    return 0


if __name__ == "__main__":
    sys.exit(main())
