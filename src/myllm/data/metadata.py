"""
Dataset metadata, manifest tracking, and statistics for MyLLM.

Serializes inspectable JSON metadata including tokenizer fingerprints,
token counts, format versions, and comprehensive dataset statistics.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional, Union

CURRENT_DATASET_FORMAT_VERSION = "1.0"


@dataclass
class DatasetMetadata:
    """Metadata manifest for a tokenized dataset."""
    format_version: str = CURRENT_DATASET_FORMAT_VERSION
    dataset_name: str = "myllm_dataset"
    tokenizer_fingerprint: str = ""
    tokenizer_vocab_size: int = 0
    dtype: str = "uint32"
    train_tokens: int = 0
    validation_tokens: int = 0
    total_tokens: int = 0
    documents_processed: int = 0
    bytes_processed: int = 0
    sequence_length: int = 128
    dataset_fingerprint: str = ""
    creation_config: Dict[str, Any] = field(default_factory=dict)
    statistics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def save(self, file_path: Union[str, Path]) -> Path:
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
        return path

    @classmethod
    def load(cls, file_path: Union[str, Path]) -> DatasetMetadata:
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(f"Dataset metadata file not found at: {path}")

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, dict):
            raise ValueError(f"Invalid dataset metadata in {path}: expected a JSON object.")

        version = data.get("format_version")
        if version != CURRENT_DATASET_FORMAT_VERSION:
            raise ValueError(
                f"Unsupported dataset format version '{version}'. Expected '{CURRENT_DATASET_FORMAT_VERSION}'."
            )

        return cls(
            format_version=data.get("format_version", CURRENT_DATASET_FORMAT_VERSION),
            dataset_name=data.get("dataset_name", "myllm_dataset"),
            tokenizer_fingerprint=data.get("tokenizer_fingerprint", ""),
            tokenizer_vocab_size=int(data.get("tokenizer_vocab_size", 0)),
            dtype=data.get("dtype", "uint32"),
            train_tokens=int(data.get("train_tokens", 0)),
            validation_tokens=int(data.get("validation_tokens", 0)),
            total_tokens=int(data.get("total_tokens", 0)),
            documents_processed=int(data.get("documents_processed", 0)),
            bytes_processed=int(data.get("bytes_processed", 0)),
            sequence_length=int(data.get("sequence_length", 128)),
            dataset_fingerprint=data.get("dataset_fingerprint", ""),
            creation_config=data.get("creation_config", {}),
            statistics=data.get("statistics", {}),
        )
