"""
Download, filter, and curate high-quality internet instruction datasets (Dolly-15k and Alpaca) for MyLLM.

Filters for:
- Concise prompt and response length (<= 80 words total) to fit CPU context window (128 tokens).
- Clear, factual, conversational categories (open QA, general QA, classification, brainstorming).
- Excludes overly long texts, complex code dumps, and formatting tables.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any, Dict, List

import pandas as pd

# Ensure UTF-8 on Windows
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def clean_text(text: str) -> str:
    """Normalize whitespace and strip unnecessary artifacts."""
    if not isinstance(text, str):
        return ""
    text = re.sub(r"\r\n", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def fetch_and_curate_dolly(target_count: int = 1500) -> List[Dict[str, str]]:
    """Download and curate high-value concise examples from Databricks Dolly-15k."""
    url = "https://huggingface.co/datasets/databricks/databricks-dolly-15k/resolve/main/databricks-dolly-15k.jsonl"
    print(f"Downloading Dolly-15k from {url}...")
    df = pd.read_json(url, lines=True)

    # Filter to most conversational/general categories
    preferred_categories = {"open_qa", "general_qa", "classification", "brainstorming", "closed_qa"}
    df = df[df["category"].isin(preferred_categories)]

    curated = []
    for _, row in df.iterrows():
        inst = clean_text(row.get("instruction", ""))
        context = clean_text(row.get("context", ""))
        resp = clean_text(row.get("response", ""))

        if not inst or not resp:
            continue

        # Reject if overly long
        inst_words = len(inst.split())
        resp_words = len(resp.split())
        context_words = len(context.split()) if context else 0

        # We want concise Q&A that fits easily within ~90 tokens
        if inst_words + resp_words + context_words > 75:
            continue
        if resp_words < 2 or inst_words < 3:
            continue
        if "http" in inst or "http" in resp:
            continue

        inp = context if context else ""
        curated.append({
            "instruction": inst,
            "input": inp,
            "output": resp,
            "source": "dolly-15k",
        })

        if len(curated) >= target_count:
            break

    print(f"Curated {len(curated)} high-quality concise examples from Dolly-15k.")
    return curated


def fetch_and_curate_alpaca(target_count: int = 1500) -> List[Dict[str, str]]:
    """Download and curate high-value concise examples from Stanford Alpaca."""
    url = "https://raw.githubusercontent.com/tatsu-lab/stanford_alpaca/main/alpaca_data.json"
    print(f"Downloading Alpaca data from {url}...")
    df = pd.read_json(url)

    curated = []
    for _, row in df.iterrows():
        inst = clean_text(row.get("instruction", ""))
        inp = clean_text(row.get("input", ""))
        resp = clean_text(row.get("output", ""))

        if not inst or not resp:
            continue

        inst_words = len(inst.split())
        resp_words = len(resp.split())
        inp_words = len(inp.split()) if inp else 0

        if inst_words + resp_words + inp_words > 75:
            continue
        if resp_words < 2 or inst_words < 3:
            continue
        if "```" in resp or "http" in resp or "def " in resp:
            continue

        curated.append({
            "instruction": inst,
            "input": inp if inp else "",
            "output": resp,
            "source": "alpaca",
        })

        if len(curated) >= target_count:
            break

    print(f"Curated {len(curated)} high-quality concise examples from Alpaca.")
    return curated


def main() -> int:
    parser = argparse.ArgumentParser(description="Download and curate internet datasets for MyLLM.")
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="data/instructions/internet_curated.jsonl",
        help="Target output JSONL path.",
    )
    parser.add_argument("--dolly-count", type=int, default=1200)
    parser.add_argument("--alpaca-count", type=int, default=1300)
    args = parser.parse_args()

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    all_examples: List[Dict[str, str]] = []

    # 1. Dolly
    dolly_data = fetch_and_curate_dolly(target_count=args.dolly_count)
    all_examples.extend(dolly_data)

    # 2. Alpaca
    alpaca_data = fetch_and_curate_alpaca(target_count=args.alpaca_count)
    all_examples.extend(alpaca_data)

    # Deduplicate by instruction
    seen_instructions = set()
    unique_examples = []
    for ex in all_examples:
        key = ex["instruction"].strip().lower()
        if key not in seen_instructions:
            seen_instructions.add(key)
            unique_examples.append({
                "instruction": ex["instruction"],
                "input": ex["input"],
                "output": ex["output"],
            })

    # Shuffle deterministically
    import random
    rng = random.Random(42)
    rng.shuffle(unique_examples)

    with open(out_path, "w", encoding="utf-8") as f:
        for ex in unique_examples:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")

    print(f"Successfully saved {len(unique_examples)} curated internet examples to {out_path.resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
