"""
Memory-mapped TokenDataset for MyLLM.

Uses np.memmap for zero-copy binary token reading and supports both
cross-document continuous sampling and strict document-bounded sequence sampling.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, List, Optional, Tuple, Union
import numpy as np

logger = logging.getLogger(__name__)

DEFAULT_DTYPE = np.uint32
INDEX_DTYPE = np.uint64


class TokenDataset:
    """
    Memory-Mapped Token Dataset.

    Exposes indexed access to training pairs (x, y) where:
        x = tokens[pos : pos + sequence_length]
        y = tokens[pos + 1 : pos + sequence_length + 1]  (next-token target)
    """

    def __init__(
        self,
        bin_path: Union[str, Path],
        sequence_length: int = 128,
        allow_cross_document_sequences: bool = False,
        idx_path: Optional[Union[str, Path]] = None,
        dtype: Union[np.dtype, type] = DEFAULT_DTYPE,
    ) -> None:
        self.bin_path = Path(bin_path)
        if not self.bin_path.is_file():
            raise FileNotFoundError(f"Binary token file not found at: {self.bin_path}")

        if sequence_length <= 0:
            raise ValueError(f"sequence_length must be positive, got {sequence_length}")

        self.sequence_length = sequence_length
        self.allow_cross_document_sequences = allow_cross_document_sequences
        self.dtype = dtype

        # Memory-map the token array in read-only mode (zero memory load)
        if self.bin_path.stat().st_size == 0:
            self.tokens = np.empty(0, dtype=self.dtype)
            self.total_tokens = 0
            self._valid_starts = []
            return

        self.tokens = np.memmap(self.bin_path, dtype=self.dtype, mode="r")
        self.total_tokens = len(self.tokens)

        # Index mapping for sequence retrieval
        self._valid_starts: List[int] = []

        if not self.allow_cross_document_sequences:
            # Check for document index file
            candidate_idx = Path(idx_path) if idx_path else self.bin_path.with_suffix(".idx")
            if candidate_idx.is_file():
                offsets = np.fromfile(candidate_idx, dtype=INDEX_DTYPE)
                for i in range(len(offsets) - 1):
                    start = int(offsets[i])
                    end = int(offsets[i + 1])
                    doc_len = end - start
                    # Document must have at least sequence_length + 1 tokens
                    if doc_len >= self.sequence_length + 1:
                        # Add valid start positions within document
                        for offset in range(doc_len - self.sequence_length):
                            self._valid_starts.append(start + offset)
            else:
                logger.warning(
                    f"Document index not found at {candidate_idx}. Falling back to continuous indexing."
                )
                self.allow_cross_document_sequences = True

        if self.allow_cross_document_sequences:
            # All sliding window positions across the whole binary array
            max_start = max(0, self.total_tokens - self.sequence_length)
            self._valid_starts = list(range(max_start))

    def __len__(self) -> int:
        return len(self._valid_starts)

    def __getitem__(self, idx: int) -> Tuple[np.ndarray, np.ndarray]:
        """
        Retrieve (x, y) training sequence pair.

        Args:
            idx: Sample index in range [0, len(self) - 1].

        Returns:
            Tuple of (x, y) where x is input tokens of length T,
            and y is target tokens shifted by 1 of length T.
        """
        if idx < 0 or idx >= len(self):
            raise IndexError(f"Index {idx} out of range for dataset with {len(self)} samples.")

        start_pos = self._valid_starts[idx]
        # x is [pos : pos + T]
        x = np.array(self.tokens[start_pos : start_pos + self.sequence_length], dtype=np.int64)
        # y is [pos + 1 : pos + T + 1]
        y = np.array(self.tokens[start_pos + 1 : start_pos + self.sequence_length + 1], dtype=np.int64)

        return x, y

    def close(self) -> None:
        """Explicitly release the memory-mapped file resource (essential on Windows)."""
        if hasattr(self, "tokens") and self.tokens is not None:
            if hasattr(self.tokens, "_mmap") and self.tokens._mmap is not None:
                try:
                    self.tokens._mmap.close()
                except Exception:
                    pass

    def __enter__(self) -> TokenDataset:
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:
            pass

