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
    parser.add_argument(
        "--quality", "-q",
        action="store_true",
        help="Run in-depth dataset quality, distribution, and sequence capacity analysis.",
    )

    args = parser.parse_args()
    raw_path = Path(args.dataset)
    dataset_dir = raw_path.parent if raw_path.is_file() else raw_path
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

    if args.quality:
        import numpy as np
        import statistics

        print("-" * 65)
        print("Detailed Quality & Document Distribution Analysis:")

        # Read document boundaries from index files
        all_doc_lens = []
        for s in ["train", "val"]:
            idx_file = dataset_dir / f"{s}.idx"
            if idx_file.is_file() and idx_file.stat().st_size > 8:
                offsets = np.fromfile(idx_file, dtype=np.uint64)
                if len(offsets) >= 2:
                    lengths = list(np.diff(offsets))
                    all_doc_lens.extend(lengths)
                    s_mean = statistics.mean(lengths)
                    s_med = statistics.median(lengths)
                    print(f"  - {s.capitalize()} Documents        : {len(lengths):,}")
                    print(f"  - {s.capitalize()} Doc Length Range: [{min(lengths)} .. {max(lengths)}] tokens")
                    print(f"  - {s.capitalize()} Mean / Median   : {s_mean:.1f} / {s_med:.1f} tokens")

        usable_train = max(0, metadata.train_tokens - metadata.sequence_length)
        usable_val = max(0, metadata.validation_tokens - metadata.sequence_length)
        print(f"  - Usable Train Sequences   : {usable_train:,} (at seq_len={metadata.sequence_length})")
        print(f"  - Usable Val Sequences     : {usable_val:,} (at seq_len={metadata.sequence_length})")
        ratio = (metadata.validation_tokens / max(1, metadata.total_tokens)) * 100.0
        print(f"  - Validation Token Ratio   : {ratio:.2f}%")

    print("=" * 65)
    print("SUCCESS: Memory-mapped dataset inspection complete.")
    print("=" * 65)
    return 0


if __name__ == "__main__":
    sys.exit(main())
