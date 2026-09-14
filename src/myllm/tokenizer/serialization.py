"""
Safe and inspectable JSON serialization for MyLLM Tokenizer.

Stores format version, special tokens, base vocabulary parameters,
ordered BPE merges, and configuration in human-readable JSON.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple, Union
from myllm.tokenizer.vocabulary import BASE_VOCAB_SIZE, Vocabulary

CURRENT_FORMAT_VERSION = "1.0"
TOKENIZER_TYPE = "byte_level_bpe"


def tokenizer_to_dict(
    vocab: Vocabulary,
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Serialize Vocabulary and tokenizer metadata to an inspectable dictionary."""
    return {
        "format_version": CURRENT_FORMAT_VERSION,
        "type": TOKENIZER_TYPE,
        "base_vocab_size": BASE_VOCAB_SIZE,
        "vocab_size": len(vocab),
        "special_tokens": vocab.special_tokens,
        "merges": [list(pair) for pair in vocab.merges_list],
        "config": config or {},
    }


def dict_to_vocabulary(data: Dict[str, Any]) -> Tuple[Vocabulary, Dict[str, Any]]:
    """
    Reconstruct a Vocabulary instance and configuration dictionary from serialized data.

    Raises:
        ValueError: If data is malformed, has an unsupported format version or invalid merges.
    """
    version = data.get("format_version")
    if version != CURRENT_FORMAT_VERSION:
        raise ValueError(
            f"Unsupported tokenizer format version '{version}'. Expected '{CURRENT_FORMAT_VERSION}'."
        )

    tokenizer_type = data.get("type")
    if tokenizer_type != TOKENIZER_TYPE:
        raise ValueError(
            f"Unsupported tokenizer type '{tokenizer_type}'. Expected '{TOKENIZER_TYPE}'."
        )

    merges_raw = data.get("merges")
    if not isinstance(merges_raw, list):
        raise ValueError("Malformed tokenizer data: 'merges' must be a list.")

    vocab = Vocabulary()

    for idx, pair in enumerate(merges_raw):
        if not (isinstance(pair, (list, tuple)) and len(pair) == 2):
            raise ValueError(f"Merge entry at index {idx} must be a 2-element tuple/list, got {pair}.")
        tok_a, tok_b = int(pair[0]), int(pair[1])
        vocab.add_merge(tok_a, tok_b)

    expected_size = data.get("vocab_size")
    if expected_size is not None and len(vocab) != int(expected_size):
        raise ValueError(
            f"Reconstructed vocabulary size {len(vocab)} does not match expected size {expected_size}."
        )

    config = data.get("config", {})
    return vocab, config


def save_tokenizer_json(
    vocab: Vocabulary,
    file_path: Union[str, Path],
    config: Optional[Dict[str, Any]] = None,
    indent: int = 2,
) -> Path:
    """Save tokenizer state to a JSON file."""
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = tokenizer_to_dict(vocab, config=config)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)

    return path


def load_tokenizer_json(file_path: Union[str, Path]) -> Tuple[Vocabulary, Dict[str, Any]]:
    """Load tokenizer state from a JSON file."""
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Tokenizer file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        raise ValueError(f"Invalid tokenizer JSON format in {path}: expected a JSON object.")

    return dict_to_vocabulary(data)
