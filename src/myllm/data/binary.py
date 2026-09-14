"""
Binary dataset writer and memory-mapping storage for MyLLM.

Writes streaming uint32 token binary files (train.bin, val.bin),
document offset index files (train.idx, val.idx), and metadata manifests.
"""

from __future__ import annotations

import hashlib
import json
import logging
import random
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Set, Tuple, Union
import numpy as np
from myllm.config import DataConfig
from myllm.data.corpus import CorpusReader
from myllm.data.metadata import CURRENT_DATASET_FORMAT_VERSION, DatasetMetadata
from myllm.data.text import normalize_text
from myllm.data.tokenizer_pipeline import TokenizerPipeline

logger = logging.getLogger(__name__)

TOKEN_DTYPE = np.uint32
INDEX_DTYPE = np.uint64


def compute_dataset_fingerprint(
    tokenizer_fingerprint: str,
    creation_config: Dict[str, Any],
    train_tokens: int,
    val_tokens: int,
    total_docs: int,
    total_bytes: int,
) -> str:
    """Compute a deterministic SHA-256 fingerprint for a built dataset."""
    canonical_repr = (
        f"tok_fp:{tokenizer_fingerprint}|"
        f"train_tokens:{train_tokens}|"
        f"val_tokens:{val_tokens}|"
        f"docs:{total_docs}|"
        f"bytes:{total_bytes}|"
        f"cfg:{sorted(creation_config.items())}"
    )
    return hashlib.sha256(canonical_repr.encode("utf-8")).hexdigest()


class BinaryDatasetWriter:
    """
    Streams corpus documents, tokenizes them, and writes uint32 binary token files
    and uint64 document boundary index files.
    """

    def __init__(
        self,
        output_dir: Union[str, Path],
        tokenizer_pipeline: TokenizerPipeline,
        config: Optional[DataConfig] = None,
    ) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.tokenizer_pipeline = tokenizer_pipeline
        self.config = config or DataConfig()

    def build_from_corpus(self, corpus_reader: CorpusReader) -> DatasetMetadata:
        """
        Ingest corpus, tokenize documents, and write train/val binary datasets.

        Document-level splitting uses a seeded PRNG to assign each document
        strictly to train or validation, preventing token leakage.
        """
        train_bin_path = self.output_dir / "train.bin"
        val_bin_path = self.output_dir / "val.bin"
        train_idx_path = self.output_dir / "train.idx"
        val_idx_path = self.output_dir / "val.idx"

        train_tokens = 0
        val_tokens = 0
        total_docs = 0
        total_bytes = 0
        unique_tokens_seen: Set[int] = set()

        doc_lengths: List[int] = []

        # Deterministic document splitting using seeded Random
        split_rng = random.Random(self.config.seed)

        with open(train_bin_path, "wb") as f_train, \
             open(val_bin_path, "wb") as f_val, \
             open(train_idx_path, "wb") as f_train_idx, \
             open(val_idx_path, "wb") as f_val_idx:

            # Write initial document offset 0 to index files
            f_train_idx.write(np.uint64(0).tobytes())
            f_val_idx.write(np.uint64(0).tobytes())

            for doc_text, source_id in corpus_reader.iter_documents():
                # 1. Text Normalization
                cleaned_text = normalize_text(
                    text=doc_text,
                    strip_bom=self.config.strip_bom,
                    normalize_newlines=self.config.normalize_newlines,
                    normalize_unicode=self.config.normalize_unicode,
                    strip_outer_whitespace=self.config.strip_outer_whitespace,
                )

                if not cleaned_text:
                    continue

                total_docs += 1
                total_bytes += len(cleaned_text.encode("utf-8"))

                # 2. Tokenize document
                tokens = self.tokenizer_pipeline.encode_document(
                    text=cleaned_text,
                    add_bos=self.config.add_bos,
                    add_eos=self.config.add_eos,
                )

                if not tokens:
                    continue

                token_count = len(tokens)
                doc_lengths.append(token_count)
                unique_tokens_seen.update(tokens)

                # 3. Determine train vs val split at document level
                # If validation_ratio == 0.0, always train
                if self.config.validation_ratio <= 0.0:
                    is_val = False
                else:
                    is_val = split_rng.random() < self.config.validation_ratio

                token_bytes = np.array(tokens, dtype=TOKEN_DTYPE).tobytes()

                if is_val:
                    f_val.write(token_bytes)
                    val_tokens += token_count
                    f_val_idx.write(np.uint64(val_tokens).tobytes())
                else:
                    f_train.write(token_bytes)
                    train_tokens += token_count
                    f_train_idx.write(np.uint64(train_tokens).tobytes())

        total_tokens = train_tokens + val_tokens

        # Calculate statistics
        avg_tokens = (sum(doc_lengths) / len(doc_lengths)) if doc_lengths else 0.0
        min_tokens = min(doc_lengths) if doc_lengths else 0
        max_tokens = max(doc_lengths) if doc_lengths else 0
        vocab_utilization = (len(unique_tokens_seen) / self.tokenizer_pipeline.vocab_size) * 100.0

        stats = {
            "average_tokens_per_document": round(avg_tokens, 2),
            "min_tokens_per_document": min_tokens,
            "max_tokens_per_document": max_tokens,
            "unique_tokens_observed": len(unique_tokens_seen),
            "vocab_utilization_percent": round(vocab_utilization, 2),
        }

        creation_cfg = {
            "validation_ratio": self.config.validation_ratio,
            "sequence_length": self.config.sequence_length,
            "add_bos": self.config.add_bos,
            "add_eos": self.config.add_eos,
            "allow_cross_document_sequences": self.config.allow_cross_document_sequences,
            "seed": self.config.seed,
        }

        dataset_fp = compute_dataset_fingerprint(
            tokenizer_fingerprint=self.tokenizer_pipeline.fingerprint,
            creation_config=creation_cfg,
            train_tokens=train_tokens,
            val_tokens=val_tokens,
            total_docs=total_docs,
            total_bytes=total_bytes,
        )

        metadata = DatasetMetadata(
            format_version=CURRENT_DATASET_FORMAT_VERSION,
            dataset_name=self.output_dir.name,
            tokenizer_fingerprint=self.tokenizer_pipeline.fingerprint,
            tokenizer_vocab_size=self.tokenizer_pipeline.vocab_size,
            dtype=str(np.dtype(TOKEN_DTYPE).name),
            train_tokens=train_tokens,
            validation_tokens=val_tokens,
            total_tokens=total_tokens,
            documents_processed=total_docs,
            bytes_processed=total_bytes,
            sequence_length=self.config.sequence_length,
            dataset_fingerprint=dataset_fp,
            creation_config=creation_cfg,
            statistics=stats,
        )

        metadata.save(self.output_dir / "metadata.json")
        logger.info(
            f"Dataset built successfully: {total_docs} docs, {total_tokens} tokens "
            f"(train={train_tokens}, val={val_tokens})."
        )
        return metadata
