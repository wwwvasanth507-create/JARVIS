"""
Supervised Instruction-Tuning (SFT) Data Pipeline for MyLLM.

Provides:
- InstructionExample dataclass with strict schema validation.
- Deterministic instruction serialization templates (Phase 7 standard).
- Tokenization with response-only loss masking (labels[i] = -100 for prompt tokens).
- Context length enforcement with prompt truncation and response preservation.
- Deterministic train/validation splitting with cross-split leakage detection.
- Memory-mapped / array-backed InstructionDataset yielding (input_ids, labels) pairs.
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Sequence, Tuple, Union
import numpy as np

from myllm.tokenizer.tokenizer import Tokenizer
from myllm.tokenizer.vocabulary import EOS_ID, PAD_ID

logger = logging.getLogger(__name__)

INSTRUCTION_TEMPLATE_VERSION = "1.0"
IGNORE_INDEX = -100


@dataclass
class InstructionExample:
    """
    A single supervised instruction-tuning example.

    Fields:
        instruction: Primary task description or directive (required, non-empty).
        input: Optional context or supplementary input text (default: "").
        output: Expected ground truth assistant completion (required, non-empty).
    """

    instruction: str
    input: str = ""
    output: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.instruction, str) or not self.instruction.strip():
            raise ValueError("InstructionExample 'instruction' must be a non-empty string.")
        if not isinstance(self.input, str):
            raise ValueError("InstructionExample 'input' must be a string.")
        if not isinstance(self.output, str) or not self.output.strip():
            raise ValueError("InstructionExample 'output' must be a non-empty string.")

        self.instruction = self.instruction.strip()
        self.input = self.input.strip()
        self.output = self.output.strip()

    def to_dict(self) -> Dict[str, str]:
        return {
            "instruction": self.instruction,
            "input": self.input,
            "output": self.output,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> InstructionExample:
        if not isinstance(data, dict):
            raise TypeError(f"Expected dict for InstructionExample, got {type(data).__name__}.")
        return cls(
            instruction=data.get("instruction", ""),
            input=data.get("input", ""),
            output=data.get("output", ""),
        )

    def content_hash(self) -> str:
        """Compute SHA-256 digest of canonical text content for deduplication."""
        canonical = f"inst:{self.instruction}|inp:{self.input}|out:{self.output}"
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class InstructionTemplate:
    """
    Deterministic serialization template for instruction examples.

    Format:
        ### Instruction:
        {instruction}

        ### Input:
        {input}

        ### Response:
        {output}
    """

    VERSION = INSTRUCTION_TEMPLATE_VERSION

    @classmethod
    def format_prompt(cls, example: InstructionExample) -> str:
        """Format the conditioning context (instruction + optional input + response header)."""
        if example.input:
            return (
                f"### Instruction:\n{example.instruction}\n\n"
                f"### Input:\n{example.input}\n\n"
                f"### Response:\n"
            )
        return f"### Instruction:\n{example.instruction}\n\n### Response:\n"

    @classmethod
    def format_full(cls, example: InstructionExample) -> str:
        """Format the complete instruction example text including response."""
        return f"{cls.format_prompt(example)}{example.output}"


@dataclass
class TokenizedInstruction:
    """Container for tokenized instruction example."""

    input_ids: np.ndarray  # [T] int64
    labels: np.ndarray     # [T] int64 with IGNORE_INDEX (-100) on prompt/pad positions
    prompt_len: int
    response_len: int
    total_len: int
    was_truncated: bool
    status: str            # "ok", "truncated_prompt", "response_too_long"


def tokenize_instruction_example(
    example: InstructionExample,
    tokenizer: Tokenizer,
    max_seq_len: int,
    mask_prompt_labels: bool = True,
    supervise_eos: bool = True,
    pad_to_max: bool = True,
) -> Tuple[Optional[TokenizedInstruction], Optional[str]]:
    """
    Tokenize an instruction example into fixed-length input_ids and response-masked labels.

    Args:
        example: The instruction example.
        tokenizer: MyLLM Byte-Level BPE tokenizer.
        max_seq_len: Maximum context window length.
        mask_prompt_labels: If True, prompt positions receive IGNORE_INDEX (-100).
        supervise_eos: If True, append tokenizer EOS token to response and supervise it.
        pad_to_max: If True, pad sequence with PAD_ID to max_seq_len.

    Returns:
        Tuple of (TokenizedInstruction, error_reason). error_reason is None on success.
    """
    prompt_text = InstructionTemplate.format_prompt(example)
    prompt_ids = tokenizer.encode(prompt_text, add_bos=False, add_eos=False)
    response_ids = tokenizer.encode(example.output, add_bos=False, add_eos=False)

    if supervise_eos:
        response_ids.append(tokenizer.eos_token_id)

    resp_len = len(response_ids)
    if resp_len >= max_seq_len:
        return None, f"response_too_long: response ({resp_len} tokens) >= max_seq_len ({max_seq_len})"

    orig_prompt_len = len(prompt_ids)
    total_unpadded = orig_prompt_len + resp_len
    was_truncated = False

    # Truncate prompt from left if combined exceeds max_seq_len
    if total_unpadded > max_seq_len:
        available_for_prompt = max_seq_len - resp_len
        prompt_ids = prompt_ids[-available_for_prompt:]
        was_truncated = True

    curr_prompt_len = len(prompt_ids)
    input_ids_list = prompt_ids + response_ids

    if mask_prompt_labels:
        labels_list = [IGNORE_INDEX] * curr_prompt_len + response_ids
    else:
        labels_list = list(input_ids_list)

    # Pad to max_seq_len if requested
    if pad_to_max:
        pad_len = max_seq_len - len(input_ids_list)
        if pad_len > 0:
            input_ids_list = input_ids_list + [PAD_ID] * pad_len
            labels_list = labels_list + [IGNORE_INDEX] * pad_len

    tokenized = TokenizedInstruction(
        input_ids=np.array(input_ids_list, dtype=np.int64),
        labels=np.array(labels_list, dtype=np.int64),
        prompt_len=curr_prompt_len,
        response_len=resp_len,
        total_len=curr_prompt_len + resp_len,
        was_truncated=was_truncated,
        status="truncated_prompt" if was_truncated else "ok",
    )
    return tokenized, None


def load_instruction_jsonl(file_path: Union[str, Path]) -> Tuple[List[InstructionExample], List[Dict[str, Any]]]:
    """
    Parse instruction examples from a JSONL file.

    Returns:
        Tuple of (valid_examples, malformed_records).
    """
    p = Path(file_path)
    if not p.is_file():
        raise FileNotFoundError(f"Instruction JSONL file not found at: {p}")

    valid: List[InstructionExample] = []
    malformed: List[Dict[str, Any]] = []

    with open(p, "r", encoding="utf-8") as f:
        for line_idx, line in enumerate(f, start=1):
            line_str = line.strip()
            if not line_str:
                continue
            try:
                data = json.loads(line_str)
                example = InstructionExample.from_dict(data)
                valid.append(example)
            except Exception as e:
                malformed.append({
                    "line": line_idx,
                    "content": line_str[:100],
                    "error": str(e),
                })

    return valid, malformed


def split_instruction_dataset(
    examples: Sequence[InstructionExample],
    val_ratio: float = 0.15,
    seed: int = 42,
) -> Tuple[List[InstructionExample], List[InstructionExample], Dict[str, Any]]:
    """
    Deterministically split instruction examples into train and validation sets.

    Ensures zero cross-split exact duplicates via SHA-256 hash sets.
    """
    if not examples:
        raise ValueError("Cannot split empty instruction examples list.")
    if not (0.0 < val_ratio < 1.0):
        raise ValueError(f"val_ratio must be in (0.0, 1.0), got {val_ratio}")

    # Deduplicate within dataset first, preserving order
    seen_hashes: set[str] = set()
    unique_examples: List[InstructionExample] = []
    intra_duplicates = 0

    for ex in examples:
        h = ex.content_hash()
        if h in seen_hashes:
            intra_duplicates += 1
            continue
        seen_hashes.add(h)
        unique_examples.append(ex)

    # Deterministic split using SHA-256 document hash modulo
    train_examples: List[InstructionExample] = []
    val_examples: List[InstructionExample] = []

    val_threshold = int(val_ratio * 10000)

    for ex in unique_examples:
        # Hash with seed for deterministic assignment
        salted = f"{seed}_{ex.content_hash()}"
        digest_int = int(hashlib.sha256(salted.encode("utf-8")).hexdigest()[:8], 16)
        bucket = digest_int % 10000
        if bucket < val_threshold:
            val_examples.append(ex)
        else:
            train_examples.append(ex)

    # Guarantee at least 1 validation example if multiple examples exist
    if len(val_examples) == 0 and len(train_examples) > 1:
        val_examples.append(train_examples.pop())
    elif len(train_examples) == 0 and len(val_examples) > 1:
        train_examples.append(val_examples.pop())

    # Verify zero cross-split leakage
    train_hashes = {ex.content_hash() for ex in train_examples}
    val_hashes = {ex.content_hash() for ex in val_examples}
    cross_overlap = train_hashes.intersection(val_hashes)

    stats = {
        "total_input_examples": len(examples),
        "unique_examples": len(unique_examples),
        "intra_duplicates": intra_duplicates,
        "train_examples": len(train_examples),
        "val_examples": len(val_examples),
        "val_ratio": len(val_examples) / max(1, len(unique_examples)),
        "cross_split_duplicates": len(cross_overlap),
        "leakage_detected": len(cross_overlap) > 0,
        "seed": seed,
    }
    return train_examples, val_examples, stats


class InstructionDataset:
    """
    Indexed Dataset yielding (input_ids, labels) pairs for SFT.

    Can be backed by in-memory numpy arrays or memory-mapped binary files.
    """

    def __init__(
        self,
        bin_path: Optional[Union[str, Path]] = None,
        examples: Optional[Sequence[TokenizedInstruction]] = None,
        sequence_length: int = 64,
    ) -> None:
        self.sequence_length = sequence_length
        self._mmap: Optional[np.memmap] = None

        if examples is not None:
            # In-memory backing
            n = len(examples)
            self.input_ids = np.zeros((n, sequence_length), dtype=np.int64)
            self.labels = np.zeros((n, sequence_length), dtype=np.int64)
            for i, ex in enumerate(examples):
                self.input_ids[i] = ex.input_ids
                self.labels[i] = ex.labels
            self.length = n
        elif bin_path is not None:
            p = Path(bin_path)
            if not p.is_file():
                raise FileNotFoundError(f"Instruction binary file not found: {p}")
            file_size = p.stat().st_size
            item_bytes = 2 * sequence_length * 8  # 2 tensors * sequence_length * int64 (8 bytes)
            if file_size % item_bytes != 0:
                raise ValueError(
                    f"File size {file_size} is not a multiple of example size {item_bytes} "
                    f"(2 * {sequence_length} * 8 bytes)."
                )
            self.length = file_size // item_bytes
            self._mmap = np.memmap(p, dtype=np.int64, mode="r", shape=(self.length, 2, sequence_length))
            self.input_ids = self._mmap[:, 0, :]
            self.labels = self._mmap[:, 1, :]
        else:
            raise ValueError("Either bin_path or examples must be provided to InstructionDataset.")

    def __len__(self) -> int:
        return self.length

    def __getitem__(self, idx: int) -> Tuple[np.ndarray, np.ndarray]:
        if idx < 0 or idx >= self.length:
            raise IndexError(f"Index {idx} out of range [0, {self.length}).")
        return self.input_ids[idx], self.labels[idx]

    def close(self) -> None:
        if self._mmap is not None:
            try:
                self._mmap._mmap.close()  # type: ignore[union-attr]
            except Exception:
                pass
            self._mmap = None

    def __enter__(self) -> InstructionDataset:
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()


def save_instruction_binary(
    tokenized_examples: Sequence[TokenizedInstruction],
    output_bin: Union[str, Path],
    sequence_length: int,
) -> int:
    """Save tokenized instructions to binary file layout: [N, 2, sequence_length] int64."""
    out_path = Path(output_bin)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    n = len(tokenized_examples)
    arr = np.zeros((n, 2, sequence_length), dtype=np.int64)
    for i, ex in enumerate(tokenized_examples):
        arr[i, 0] = ex.input_ids
        arr[i, 1] = ex.labels

    arr.tofile(out_path)
    return n
