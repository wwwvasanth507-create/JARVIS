"""
Deterministic Byte-Level BPE Trainer for MyLLM.

Trains a vocabulary of merges from an iterable of documents or text files
using a strictly deterministic tie-breaking strategy on CPU.
"""

from __future__ import annotations

import logging
from collections import Counter
from typing import Dict, Iterable, List, Optional, Tuple
from myllm.tokenizer.bpe import chunk_to_byte_tokens, split_text_into_chunks
from myllm.tokenizer.vocabulary import BASE_VOCAB_SIZE, Vocabulary

logger = logging.getLogger(__name__)


class BPETrainer:
    """
    Byte-Level BPE Trainer.

    Learns adjacent byte/token pair merges iteratively until target vocab_size
    or min_frequency threshold is reached.

    Tie-Breaking Strategy:
        When multiple pairs have the identical maximum frequency, the pair with the
        lowest integer token IDs is selected: sorting key is (-frequency, pair[0], pair[1]).
        This guarantees complete, cross-platform mathematical determinism.
    """

    def __init__(
        self,
        vocab_size: int = 1000,
        min_pair_frequency: int = 2,
        max_documents: Optional[int] = None,
        max_training_bytes: Optional[int] = None,
    ) -> None:
        if vocab_size < BASE_VOCAB_SIZE:
            raise ValueError(
                f"vocab_size ({vocab_size}) cannot be smaller than the base vocabulary "
                f"size of {BASE_VOCAB_SIZE} (4 special tokens + 256 bytes)."
            )
        if min_pair_frequency < 1:
            raise ValueError(f"min_pair_frequency must be at least 1, got {min_pair_frequency}.")

        self.vocab_size = vocab_size
        self.min_pair_frequency = min_pair_frequency
        self.max_documents = max_documents
        self.max_training_bytes = max_training_bytes

    def train(self, corpus: Iterable[str]) -> Tuple[Vocabulary, List[Tuple[int, int]]]:
        """
        Train BPE merges on the given text corpus.

        Args:
            corpus: An iterable yielding text documents.

        Returns:
            Tuple of (Vocabulary instance, list of learned merge pairs).
        """
        vocab = Vocabulary()
        target_merges = self.vocab_size - BASE_VOCAB_SIZE
        if target_merges <= 0:
            return vocab, []

        # 1. Ingest corpus and build initial chunk frequency table
        chunk_freqs: Counter[Tuple[int, ...]] = Counter()
        total_docs = 0
        total_bytes = 0

        for doc in corpus:
            if not doc:
                continue

            doc_bytes = len(doc.encode("utf-8"))
            if self.max_training_bytes and (total_bytes + doc_bytes) > self.max_training_bytes:
                break

            total_docs += 1
            total_bytes += doc_bytes

            chunks = split_text_into_chunks(doc)
            for chunk in chunks:
                initial_tokens = tuple(chunk_to_byte_tokens(chunk))
                chunk_freqs[initial_tokens] += 1

            if self.max_documents and total_docs >= self.max_documents:
                break

        logger.info(
            f"BPE Ingestion complete: {total_docs} documents, {total_bytes} bytes, "
            f"{len(chunk_freqs)} unique chunk forms."
        )

        # 2. Iteratively learn merges
        learned_merges: List[Tuple[int, int]] = []

        for step in range(target_merges):
            # Count adjacent token pairs
            pair_counts: Counter[Tuple[int, int]] = Counter()
            for chunk_tuple, freq in chunk_freqs.items():
                if len(chunk_tuple) < 2:
                    continue
                for i in range(len(chunk_tuple) - 1):
                    pair = (chunk_tuple[i], chunk_tuple[i + 1])
                    pair_counts[pair] += freq

            if not pair_counts:
                logger.info(f"No further candidate pairs found at step {step}. Training stopped.")
                break

            # Find candidates with frequency >= min_pair_frequency
            eligible_pairs = [
                (pair, count)
                for pair, count in pair_counts.items()
                if count >= self.min_pair_frequency
            ]

            if not eligible_pairs:
                logger.info(
                    f"No pairs meet min_pair_frequency ({self.min_pair_frequency}) at step {step}. "
                    f"Training stopped."
                )
                break

            # Deterministic tie-breaking:
            # Sort by (-frequency, pair[0], pair[1])
            best_pair, best_freq = min(
                eligible_pairs,
                key=lambda item: (-item[1], item[0][0], item[0][1]),
            )

            # Add merge to vocabulary
            target_a, target_b = best_pair
            new_id = vocab.add_merge(target_a, target_b)
            learned_merges.append(best_pair)

            # Update chunk frequencies by replacing (target_a, target_b) with new_id
            new_chunk_freqs: Counter[Tuple[int, ...]] = Counter()
            for chunk_tuple, freq in chunk_freqs.items():
                if len(chunk_tuple) < 2:
                    new_chunk_freqs[chunk_tuple] += freq
                    continue

                # Check if target pair appears in chunk_tuple
                has_pair = False
                for i in range(len(chunk_tuple) - 1):
                    if chunk_tuple[i] == target_a and chunk_tuple[i + 1] == target_b:
                        has_pair = True
                        break

                if not has_pair:
                    new_chunk_freqs[chunk_tuple] += freq
                    continue

                # Replace occurrences of target pair
                new_tokens: List[int] = []
                idx = 0
                while idx < len(chunk_tuple):
                    if (
                        idx < len(chunk_tuple) - 1
                        and chunk_tuple[idx] == target_a
                        and chunk_tuple[idx + 1] == target_b
                    ):
                        new_tokens.append(new_id)
                        idx += 2
                    else:
                        new_tokens.append(chunk_tuple[idx])
                        idx += 1

                new_chunk_freqs[tuple(new_tokens)] += freq

            chunk_freqs = new_chunk_freqs

        logger.info(
            f"BPE Training complete. Learned {len(learned_merges)} merges. "
            f"Final vocabulary size: {len(vocab)}."
        )

        return vocab, learned_merges
