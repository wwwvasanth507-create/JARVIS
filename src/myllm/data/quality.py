"""
Dataset Quality Validation and Data Leakage Detection for MyLLM.

Analyzes raw text corpora and tokenized datasets to verify:
- Document lengths (min, max, mean, median) and token counts.
- Empty documents and normalization filtering counts.
- Exact intra-split duplicates and cross-split data leakage.
- Split ratios and sequence capacity for a target context length.
- Tokenizer and dataset cryptographic fingerprints.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
import statistics
from typing import Any, Dict, List, Optional, Set, Tuple
from myllm.data.corpus import CorpusReader
from myllm.data.dataset import TokenDataset
from myllm.data.metadata import DatasetMetadata
from myllm.data.text import normalize_text
from myllm.tokenizer import Tokenizer


@dataclass
class DatasetQualityReport:
    """Comprehensive dataset quality, leakage, and distribution statistics."""
    total_documents: int
    total_bytes: int
    total_tokens: int
    min_doc_tokens: int
    max_doc_tokens: int
    mean_doc_tokens: float
    median_doc_tokens: float
    empty_documents_found: int
    intra_split_duplicates: int
    cross_split_duplicates: int
    train_tokens: int
    validation_tokens: int
    train_val_ratio: float
    train_documents: int
    val_documents: int
    usable_train_sequences: int
    usable_val_sequences: int
    context_length: int
    tokenizer_vocab_size: int
    tokenizer_fingerprint: str
    dataset_fingerprint: str
    split_method: str
    split_seed: Optional[int]
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def format_summary_text(self) -> str:
        """Format the report into an inspectable console report."""
        lines = [
            "=" * 65,
            "            MYLLM DATASET QUALITY & LEAKAGE REPORT             ",
            "=" * 65,
            f"Total Documents Processed   : {self.total_documents:,}",
            f"Total Raw Bytes             : {self.total_bytes:,} ({self.total_bytes / 1024:.2f} KB)",
            f"Total Tokens                : {self.total_tokens:,}",
            f"Document Token Range        : [{self.min_doc_tokens} .. {self.max_doc_tokens}]",
            f"Mean / Median Doc Tokens    : {self.mean_doc_tokens:.1f} / {self.median_doc_tokens:.1f}",
            f"Empty Documents Detected    : {self.empty_documents_found}",
            f"Intra-Split Duplicates      : {self.intra_split_duplicates}",
            f"Cross-Split Data Leakage    : {self.cross_split_duplicates} duplicate docs found",
            "-" * 65,
            f"Train / Val Documents       : {self.train_documents:,} / {self.val_documents:,}",
            f"Train / Val Tokens          : {self.train_tokens:,} / {self.validation_tokens:,}",
            f"Train / Val Token Ratio     : {self.train_val_ratio:.2f}% validation",
            f"Split Method / Seed         : {self.split_method} (seed={self.split_seed})",
            "-" * 65,
            f"Target Context Length       : {self.context_length}",
            f"Usable Train Windows        : {self.usable_train_sequences:,}",
            f"Usable Validation Windows   : {self.usable_val_sequences:,}",
            f"Tokenizer Vocab Size        : {self.tokenizer_vocab_size}",
            f"Tokenizer Fingerprint       : {self.tokenizer_fingerprint[:16]}...",
            f"Dataset Fingerprint         : {self.dataset_fingerprint[:16] if self.dataset_fingerprint else 'N/A'}...",
            "=" * 65,
        ]
        if self.warnings:
            lines.append("WARNINGS:")
            for w in self.warnings:
                lines.append(f"  [!] {w}")
            lines.append("=" * 65)
        return "\n".join(lines)


def hash_document_text(text: str) -> str:
    """Compute SHA-256 hash of normalized document text."""
    normalized = " ".join(text.split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


class DatasetQualityValidator:
    """
    Validates dataset quality and verifies strict separation between train and val splits.
    """

    @staticmethod
    def inspect_splits(
        train_docs: List[str],
        val_docs: List[str],
        tokenizer: Tokenizer,
        context_length: int = 128,
        split_method: str = "document_split",
        split_seed: Optional[int] = 42,
        dataset_fingerprint: str = "",
    ) -> DatasetQualityReport:
        """
        Inspect raw document lists for train and validation splits.

        Args:
            train_docs: List of text documents in train split.
            val_docs: List of text documents in validation split.
            tokenizer: Tokenizer instance.
            context_length: Target model context length.
            split_method: Description of split algorithm.
            split_seed: Seed used during splitting.
            dataset_fingerprint: Dataset SHA-256 fingerprint if built.

        Returns:
            DatasetQualityReport with all metrics and detected issues.
        """
        warnings: List[str] = []

        # 1. Document hashes for duplicate and leakage detection
        train_hashes: Set[str] = set()
        val_hashes: Set[str] = set()
        intra_duplicates = 0
        empty_docs = 0

        # Inspect train docs
        train_doc_lengths: List[int] = []
        train_bytes = 0
        train_tokens = 0
        for doc in train_docs:
            cleaned = normalize_text(doc)
            if not cleaned:
                empty_docs += 1
                continue
            doc_hash = hash_document_text(cleaned)
            if doc_hash in train_hashes:
                intra_duplicates += 1
            else:
                train_hashes.add(doc_hash)

            raw_bytes = len(cleaned.encode("utf-8"))
            train_bytes += raw_bytes
            toks = tokenizer.encode(cleaned)
            tok_len = len(toks)
            train_tokens += tok_len
            train_doc_lengths.append(tok_len)

        # Inspect val docs
        val_doc_lengths: List[int] = []
        val_bytes = 0
        val_tokens = 0
        cross_split_duplicates = 0
        for doc in val_docs:
            cleaned = normalize_text(doc)
            if not cleaned:
                empty_docs += 1
                continue
            doc_hash = hash_document_text(cleaned)
            if doc_hash in val_hashes:
                intra_duplicates += 1
            else:
                val_hashes.add(doc_hash)

            # Check cross-split data leakage!
            if doc_hash in train_hashes:
                cross_split_duplicates += 1

            raw_bytes = len(cleaned.encode("utf-8"))
            val_bytes += raw_bytes
            toks = tokenizer.encode(cleaned)
            tok_len = len(toks)
            val_tokens += tok_len
            val_doc_lengths.append(tok_len)

        all_lengths = train_doc_lengths + val_doc_lengths
        total_docs = len(all_lengths)
        total_tokens = train_tokens + val_tokens
        total_bytes = train_bytes + val_bytes

        if cross_split_duplicates > 0:
            warnings.append(
                f"Data leakage detected: {cross_split_duplicates} exact duplicate documents found "
                f"present in both train and validation splits!"
            )

        if total_docs == 0:
            min_len = 0
            max_len = 0
            mean_len = 0.0
            med_len = 0.0
        else:
            min_len = min(all_lengths)
            max_len = max(all_lengths)
            mean_len = float(statistics.mean(all_lengths))
            med_len = float(statistics.median(all_lengths))

        # Usable sequence windows: max(0, total_tokens - context_length)
        usable_train = max(0, train_tokens - context_length)
        usable_val = max(0, val_tokens - context_length)

        if usable_train == 0:
            warnings.append(
                f"Train tokens ({train_tokens}) is insufficient for context_length={context_length}."
            )
        if usable_val == 0 and val_tokens > 0:
            warnings.append(
                f"Val tokens ({val_tokens}) is insufficient for context_length={context_length}."
            )

        val_ratio = (val_tokens / total_tokens * 100.0) if total_tokens > 0 else 0.0

        # Cryptographic tokenizer fingerprint
        from myllm.data.tokenizer_pipeline import compute_tokenizer_fingerprint
        tok_fp = compute_tokenizer_fingerprint(tokenizer)

        return DatasetQualityReport(
            total_documents=total_docs,
            total_bytes=total_bytes,
            total_tokens=total_tokens,
            min_doc_tokens=min_len,
            max_doc_tokens=max_len,
            mean_doc_tokens=mean_len,
            median_doc_tokens=med_len,
            empty_documents_found=empty_docs,
            intra_split_duplicates=intra_duplicates,
            cross_split_duplicates=cross_split_duplicates,
            train_tokens=train_tokens,
            validation_tokens=val_tokens,
            train_val_ratio=val_ratio,
            train_documents=len(train_doc_lengths),
            val_documents=len(val_doc_lengths),
            usable_train_sequences=usable_train,
            usable_val_sequences=usable_val,
            context_length=context_length,
            tokenizer_vocab_size=len(tokenizer),
            tokenizer_fingerprint=tok_fp,
            dataset_fingerprint=dataset_fingerprint,
            split_method=split_method,
            split_seed=split_seed,
            warnings=warnings,
        )
