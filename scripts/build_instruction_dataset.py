"""
CLI Builder for Supervised Instruction-Tuning (SFT) Datasets (Phase 7).

Parses JSONL instruction files, enforces strict schema validation,
performs deterministic train/val splitting with zero cross-split leakage,
tokenizes with response-only loss masking, applies context-length policies,
writes binary memmap-compatible files, and produces detailed dataset statistics.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional

import numpy as np

from myllm.data.instruction import (
    INSTRUCTION_TEMPLATE_VERSION,
    InstructionExample,
    TokenizedInstruction,
    load_instruction_jsonl,
    save_instruction_binary,
    split_instruction_dataset,
    tokenize_instruction_example,
)
from myllm.data.tokenizer_pipeline import compute_tokenizer_fingerprint
from myllm.tokenizer.tokenizer import Tokenizer

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("build_instruction_dataset")


def compute_sft_dataset_fingerprint(
    tokenizer_fingerprint: str,
    template_version: str,
    sequence_length: int,
    train_count: int,
    val_count: int,
    train_supervised_tokens: int,
    val_supervised_tokens: int,
    seed: int,
) -> str:
    """Compute a deterministic SHA-256 fingerprint for an SFT dataset."""
    canonical = (
        f"tok_fp:{tokenizer_fingerprint}|"
        f"template:{template_version}|"
        f"seq_len:{sequence_length}|"
        f"train_ex:{train_count}|"
        f"val_ex:{val_count}|"
        f"train_sup:{train_supervised_tokens}|"
        f"val_sup:{val_supervised_tokens}|"
        f"seed:{seed}"
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def process_examples(
    examples: List[InstructionExample],
    tokenizer: Tokenizer,
    sequence_length: int,
    mask_prompt_labels: bool = True,
    supervise_eos: bool = True,
) -> Tuple[List[TokenizedInstruction], Dict[str, Any]]:
    """Tokenize a list of InstructionExample instances and aggregate statistics."""
    tokenized: List[TokenizedInstruction] = []
    rejected: List[Dict[str, Any]] = []

    prompt_lens: List[int] = []
    response_lens: List[int] = []
    supervised_lens: List[int] = []
    truncated_prompts = 0

    for idx, ex in enumerate(examples):
        # Format 1: Standard instruction format (### Instruction: ... ### Response: ...)
        tok_inst, err_inst = tokenize_instruction_example(
            example=ex,
            tokenizer=tokenizer,
            max_seq_len=sequence_length,
            mask_prompt_labels=mask_prompt_labels,
            supervise_eos=supervise_eos,
            pad_to_max=True,
            template_format="instruction",
        )
        if tok_inst is not None:
            if tok_inst.was_truncated:
                truncated_prompts += 1
            tokenized.append(tok_inst)
            prompt_lens.append(tok_inst.prompt_len)
            response_lens.append(tok_inst.response_len)
            supervised_lens.append(int(np.sum(tok_inst.labels[1:] != -100)))
        else:
            rejected.append({"index": idx, "reason": err_inst, "instruction": ex.instruction[:50]})

        # Format 2: Conversational chat format (### User: ... ### Assistant: ...)
        tok_chat, _ = tokenize_instruction_example(
            example=ex,
            tokenizer=tokenizer,
            max_seq_len=sequence_length,
            mask_prompt_labels=mask_prompt_labels,
            supervise_eos=supervise_eos,
            pad_to_max=True,
            template_format="chat",
        )
        if tok_chat is not None:
            tokenized.append(tok_chat)
            prompt_lens.append(tok_chat.prompt_len)
            response_lens.append(tok_chat.response_len)
            supervised_lens.append(int(np.sum(tok_chat.labels[1:] != -100)))

    total_tokens = sum(prompt_lens) + sum(response_lens)
    total_supervised = sum(supervised_lens)
    total_padded = len(tokenized) * sequence_length

    stats = {
        "total_examples": len(examples),
        "accepted": len(tokenized),
        "rejected": len(rejected),
        "truncated_prompts": truncated_prompts,
        "prompt_tokens": sum(prompt_lens),
        "response_tokens": sum(response_lens),
        "supervised_tokens": total_supervised,
        "total_unpadded_tokens": total_tokens,
        "total_padded_tokens": total_padded,
        "average_prompt_length": float(np.mean(prompt_lens)) if prompt_lens else 0.0,
        "average_response_length": float(np.mean(response_lens)) if response_lens else 0.0,
        "maximum_response_length": int(np.max(response_lens)) if response_lens else 0,
        "supervised_token_percent": (total_supervised / max(1, total_padded)) * 100.0,
        "rejection_details": rejected,
    }
    return tokenized, stats


def main() -> int:
    parser = argparse.ArgumentParser(description="Build binary SFT instruction dataset for MyLLM.")
    parser.add_argument(
        "--input",
        "-i",
        type=str,
        default="data/instructions/synthetic_sft.jsonl",
        help="Path to instruction JSONL file or directory.",
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        type=str,
        default="data/instruction",
        help="Target output directory for binary dataset.",
    )
    parser.add_argument(
        "--tokenizer",
        "-t",
        type=str,
        default="data/tokenized/tokenizer.json",
        help="Path to tokenizer.json.",
    )
    parser.add_argument(
        "--sequence-length",
        "-s",
        type=int,
        default=64,
        help="Target context window sequence length (default: 64).",
    )
    parser.add_argument(
        "--val-ratio",
        type=float,
        default=0.15,
        help="Validation split ratio (default: 0.15).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Deterministic random seed for split (default: 42).",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_dir = Path(args.output_dir)
    tok_path = Path(args.tokenizer)

    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load Tokenizer
    if not tok_path.is_file():
        logger.error(f"Tokenizer not found at: {tok_path}")
        return 1
    tokenizer = Tokenizer.load(tok_path)
    tok_fp = compute_tokenizer_fingerprint(tokenizer)
    logger.info(f"Loaded tokenizer from {tok_path} (vocab={len(tokenizer)}, fp={tok_fp[:16]}...)")

    # 2. Ingest JSONL files
    all_examples: List[InstructionExample] = []
    all_malformed: List[Dict[str, Any]] = []

    if input_path.is_file():
        valid, mal = load_instruction_jsonl(input_path)
        all_examples.extend(valid)
        all_malformed.extend(mal)
    elif input_path.is_dir():
        for jsonl_file in sorted(input_path.glob("*.jsonl")):
            valid, mal = load_instruction_jsonl(jsonl_file)
            all_examples.extend(valid)
            all_malformed.extend(mal)
    else:
        logger.error(f"Input path not found: {input_path}")
        return 1

    logger.info(f"Ingested {len(all_examples)} valid examples (malformed lines: {len(all_malformed)})")

    # 3. Deterministic Train/Validation Split with Leakage Detection
    train_ex, val_ex, split_stats = split_instruction_dataset(
        examples=all_examples,
        val_ratio=args.val_ratio,
        seed=args.seed,
    )
    logger.info(
        f"Split complete: {len(train_ex)} train, {len(val_ex)} val "
        f"(intra-duplicates: {split_stats['intra_duplicates']}, cross-duplicates: {split_stats['cross_split_duplicates']})"
    )
    if split_stats["leakage_detected"]:
        logger.error("Data leakage detected between train and val splits!")
        return 1

    # 4. Tokenize with Response-Only Loss Masking
    train_tok, train_stats = process_examples(
        examples=train_ex,
        tokenizer=tokenizer,
        sequence_length=args.sequence_length,
        mask_prompt_labels=True,
        supervise_eos=True,
    )
    val_tok, val_stats = process_examples(
        examples=val_ex,
        tokenizer=tokenizer,
        sequence_length=args.sequence_length,
        mask_prompt_labels=True,
        supervise_eos=True,
    )

    # 5. Save Binary Token Files
    train_bin_path = output_dir / "train_sft.bin"
    val_bin_path = output_dir / "val_sft.bin"
    save_instruction_binary(train_tok, train_bin_path, args.sequence_length)
    save_instruction_binary(val_tok, val_bin_path, args.sequence_length)

    # 6. Compute Dataset Fingerprint
    dataset_fp = compute_sft_dataset_fingerprint(
        tokenizer_fingerprint=tok_fp,
        template_version=INSTRUCTION_TEMPLATE_VERSION,
        sequence_length=args.sequence_length,
        train_count=len(train_tok),
        val_count=len(val_tok),
        train_supervised_tokens=train_stats["supervised_tokens"],
        val_supervised_tokens=val_stats["supervised_tokens"],
        seed=args.seed,
    )

    # 7. Write metadata.json manifest
    meta_payload = {
        "dataset_type": "instruction_sft",
        "format_version": "1.0",
        "template_version": INSTRUCTION_TEMPLATE_VERSION,
        "tokenizer_fingerprint": tok_fp,
        "dataset_fingerprint": dataset_fp,
        "sequence_length": args.sequence_length,
        "split_seed": args.seed,
        "split_stats": split_stats,
        "train": train_stats,
        "validation": val_stats,
        "tokenizer_vocab_size": len(tokenizer),
    }

    meta_path = output_dir / "metadata.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta_payload, f, indent=2, ensure_ascii=False)

    print("=" * 65)
    print("         MyLLM Instruction Dataset Builder Manifest             ")
    print("=" * 65)
    print(f"Output Directory        : {output_dir.resolve()}")
    print(f"Template Version        : {INSTRUCTION_TEMPLATE_VERSION}")
    print(f"Context Length          : {args.sequence_length}")
    print(f"Tokenizer Fingerprint   : {tok_fp[:16]}...")
    print(f"Dataset Fingerprint     : {dataset_fp[:16]}...")
    print("-" * 65)
    print(f"Total Ingested Examples : {len(all_examples):,}")
    print(f"Unique Examples         : {split_stats['unique_examples']:,}")
    print(f"Cross-Split Duplicates  : {split_stats['cross_split_duplicates']} (0% Leakage)")
    print("-" * 65)
    print("TRAIN SPLIT:")
    print(f"  Accepted Examples     : {train_stats['accepted']:,} (Rejected: {train_stats['rejected']})")
    print(f"  Prompt Tokens         : {train_stats['prompt_tokens']:,} (avg: {train_stats['average_prompt_length']:.1f})")
    print(f"  Response Tokens       : {train_stats['response_tokens']:,} (avg: {train_stats['average_response_length']:.1f})")
    print(f"  Supervised Loss Tokens: {train_stats['supervised_tokens']:,} ({train_stats['supervised_token_percent']:.1f}% of padded buffer)")
    print("VALIDATION SPLIT:")
    print(f"  Accepted Examples     : {val_stats['accepted']:,} (Rejected: {val_stats['rejected']})")
    print(f"  Prompt Tokens         : {val_stats['prompt_tokens']:,} (avg: {val_stats['average_prompt_length']:.1f})")
    print(f"  Response Tokens       : {val_stats['response_tokens']:,} (avg: {val_stats['average_response_length']:.1f})")
    print(f"  Supervised Loss Tokens: {val_stats['supervised_tokens']:,} ({val_stats['supervised_token_percent']:.1f}% of padded buffer)")
    print("=" * 65)
    print("SUCCESS: SFT instruction dataset created successfully.")
    print("=" * 65)
    return 0


if __name__ == "__main__":
    sys.exit(main())
