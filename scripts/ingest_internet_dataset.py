"""
Internet & Hugging Face Dataset Ingestion Utility for MyLLM.

Allows loading free open datasets from the internet via:
- Hugging Face parquet URLs: hf://datasets/<repo_id>/<file>.parquet
- HTTPS direct parquet / JSON / CSV URLs
- Local parquet files

Transforms datasets into either:
1. Pretraining corpus text (data/raw/<name>.txt)
2. SFT instruction dataset (data/instructions/<name>.jsonl)
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Optional

import pandas as pd

# Ensure UTF-8 on Windows
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def load_dataset_from_source(source_url_or_path: str) -> pd.DataFrame:
    """Load DataFrame from local path, HTTPS, or hf:// URI."""
    print(f"Loading dataset from: {source_url_or_path}...")
    if source_url_or_path.endswith(".parquet") or "hf://datasets" in source_url_or_path:
        try:
            df = pd.read_parquet(source_url_or_path)
        except Exception as e:
            print(f"Default engine failed ({e}), retrying with engine='fastparquet'...")
            df = pd.read_parquet(source_url_or_path, engine="fastparquet")
    elif source_url_or_path.endswith(".csv"):
        df = pd.read_csv(source_url_or_path)
    elif source_url_or_path.endswith(".json") or source_url_or_path.endswith(".jsonl"):
        df = pd.read_json(source_url_or_path, lines=source_url_or_path.endswith(".jsonl"))
    else:
        try:
            df = pd.read_parquet(source_url_or_path)
        except Exception:
            df = pd.read_parquet(source_url_or_path, engine="fastparquet")

    print(f"Loaded DataFrame with shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")
    return df


def inspect_dataset(df: pd.DataFrame, num_samples: int = 5) -> None:
    """Display summary and head samples."""
    print("\n" + "=" * 60)
    print("DATASET PREVIEW")
    print("=" * 60)
    print(df.head(num_samples))
    print("=" * 60 + "\n")


def convert_to_instruction_jsonl(
    df: pd.DataFrame,
    instruction_col: str,
    output_col: str,
    input_col: Optional[str] = None,
    output_file: str = "data/instructions/internet_sft.jsonl",
    max_samples: Optional[int] = None,
) -> Path:
    """Convert columns of DataFrame into MyLLM instruction JSONL format."""
    out_path = Path(output_file)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    count = 0
    with open(out_path, "w", encoding="utf-8") as f:
        for _, row in df.iterrows():
            inst = str(row.get(instruction_col, "")).strip()
            out = str(row.get(output_col, "")).strip()
            inp = str(row.get(input_col, "")).strip() if input_col and input_col in row else ""

            if not inst or not out:
                continue

            example = {
                "instruction": inst,
                "input": inp,
                "output": out,
            }
            f.write(json.dumps(example, ensure_ascii=False) + "\n")
            count += 1
            if max_samples and count >= max_samples:
                break

    print(f"Successfully exported {count} instruction examples to {out_path.resolve()}")
    return out_path


def convert_to_pretrain_corpus(
    df: pd.DataFrame,
    text_col: str,
    output_file: str = "data/raw/internet_corpus.txt",
    max_samples: Optional[int] = None,
) -> Path:
    """Convert text column of DataFrame into a raw pretraining corpus file."""
    out_path = Path(output_file)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    count = 0
    with open(out_path, "w", encoding="utf-8") as f:
        for _, row in df.iterrows():
            text = str(row.get(text_col, "")).strip()
            if not text or len(text) < 10:
                continue

            f.write(text + "\n\n")
            count += 1
            if max_samples and count >= max_samples:
                break

    print(f"Successfully exported {count} documents to {out_path.resolve()}")
    return out_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest free internet / Hugging Face datasets for MyLLM.")
    parser.add_argument(
        "--source",
        "-s",
        type=str,
        default="hf://datasets/Grio43/Tag_cleaning/merged_2026.parquet",
        help="Dataset URI or URL (e.g. hf://datasets/...)",
    )
    parser.add_argument(
        "--inspect-only",
        action="store_true",
        help="Inspect columns and exit without exporting.",
    )
    parser.add_argument(
        "--mode",
        choices=["instruction", "pretrain"],
        default="instruction",
        help="Conversion mode: 'instruction' for SFT or 'pretrain' for raw corpus.",
    )
    parser.add_argument("--instruction-col", type=str, default="instruction")
    parser.add_argument("--output-col", type=str, default="output")
    parser.add_argument("--input-col", type=str, default=None)
    parser.add_argument("--text-col", type=str, default="text")
    parser.add_argument("--output-file", "-o", type=str, default=None)
    parser.add_argument("--max-samples", type=int, default=10000)

    args = parser.parse_args()

    df = load_dataset_from_source(args.source)
    inspect_dataset(df, num_samples=3)

    if args.inspect_only:
        return 0

    if args.mode == "instruction":
        if args.instruction_col not in df.columns or args.output_col not in df.columns:
            print(
                f"Error: Columns '{args.instruction_col}' and '{args.output_col}' not both in dataset.\n"
                f"Available columns: {list(df.columns)}\n"
                f"Please specify --instruction-col and --output-col matching your dataset.",
                file=sys.stderr,
            )
            return 1
        out = args.output_file or "data/instructions/internet_sft.jsonl"
        convert_to_instruction_jsonl(
            df,
            instruction_col=args.instruction_col,
            output_col=args.output_col,
            input_col=args.input_col,
            output_file=out,
            max_samples=args.max_samples,
        )
    else:
        if args.text_col not in df.columns:
            print(
                f"Error: Text column '{args.text_col}' not in dataset.\n"
                f"Available columns: {list(df.columns)}\n"
                f"Please specify --text-col matching your dataset.",
                file=sys.stderr,
            )
            return 1
        out = args.output_file or "data/raw/internet_corpus.txt"
        convert_to_pretrain_corpus(
            df,
            text_col=args.text_col,
            output_file=out,
            max_samples=args.max_samples,
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
