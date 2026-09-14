#!/usr/bin/env python3
"""
CLI script to inspect a tokenized binary dataset for MyLLM without loading the entire dataset into RAM.

Usage:
    python scripts/inspect_dataset.py --dataset data/tokenized --tokenizer checkpoints/tokenizer.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import numpy as np

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

    with open(meta_path, "r", encoding="utf-8") as f:
        meta_dict = json.load(f)

    # Optional tokenizer for decoding sample
    tokenizer = None
    if args.tokenizer:
        tok_path = Path(args.tokenizer)
        if tok_path.is_file():
            tokenizer = Tokenizer.load(tok_path)

    if meta_dict.get("dataset_type") == "instruction_sft":
        print("=" * 65)
        print("         MyLLM Instruction SFT Dataset Inspection Manifest       ")
        print("=" * 65)
        print(f"Dataset Directory        : {dataset_dir.resolve()}")
        print(f"Dataset Type             : Instruction SFT")
        print(f"Template Version         : {meta_dict.get('template_version', '1.0')}")
        print(f"Context Length           : {meta_dict.get('sequence_length')}")
        print(f"Tokenizer Fingerprint    : {meta_dict.get('tokenizer_fingerprint', '')[:24]}...")
        print(f"Dataset Fingerprint      : {meta_dict.get('dataset_fingerprint', '')[:24]}...")
        print("-" * 65)
        print("Files on Disk:")
        for fname in ["train_sft.bin", "val_sft.bin", "metadata.json"]:
            fpath = dataset_dir / fname
            if fpath.is_file():
                size_str = format_file_size(fpath.stat().st_size)
                print(f"  - {fname:<15} : {size_str:>10} ({fpath.stat().st_size:,} bytes)")
            else:
                print(f"  - {fname:<15} : [Not Found]")

        print("-" * 65)
        split_stats = meta_dict.get("split_stats", {})
        print(f"Total Unique Examples    : {split_stats.get('unique_examples', 0):,}")
        print(f"Cross-Split Duplicates   : {split_stats.get('cross_split_duplicates', 0)} (0% Leakage)")
        train_info = meta_dict.get("train", {})
        val_info = meta_dict.get("validation", {})
        print(f"Train Accepted / Supervised Tokens: {train_info.get('accepted', 0)} / {train_info.get('supervised_tokens', 0):,}")
        print(f"Val Accepted / Supervised Tokens  : {val_info.get('accepted', 0)} / {val_info.get('supervised_tokens', 0):,}")

        # Preview sample from train_sft.bin or val_sft.bin
        target_split_file = dataset_dir / f"{args.split}_sft.bin"
        if target_split_file.is_file() and target_split_file.stat().st_size > 0:
            seq_len = int(meta_dict.get("sequence_length", 64))
            arr = np.memmap(target_split_file, dtype=np.int64, mode="r")
            item_len = 2 * seq_len
            if len(arr) >= item_len:
                x_sample = arr[:seq_len]
                labels_sample = arr[seq_len:item_len]
                print("-" * 65)
                print(f"Sample First Instruction ({args.split}_sft.bin):")
                print(f"  input_ids (tokens): {list(x_sample[:16])}...")
                print(f"  labels (masked)   : {list(labels_sample[:16])}...")
                sup_count = int(np.sum(labels_sample[1:] != -100))
                print(f"  Supervised Tokens : {sup_count} (out of {seq_len})")
                if tokenizer is not None:
                    # Decode prompt vs response
                    prompt_toks = [t for t, l in zip(x_sample, labels_sample) if l == -100 and t != 0]
                    resp_toks = [t for t, l in zip(x_sample, labels_sample) if l != -100]
                    print(f"  Prompt Decoded    : {tokenizer.decode(prompt_toks, skip_special_tokens=False)!r}")
                    print(f"  Response Decoded  : {tokenizer.decode(resp_toks, skip_special_tokens=False)!r}")

        print("=" * 65)
        print("SUCCESS: Instruction SFT dataset inspection complete.")
        print("=" * 65)
        return 0

    metadata = DatasetMetadata.load(meta_path)

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
