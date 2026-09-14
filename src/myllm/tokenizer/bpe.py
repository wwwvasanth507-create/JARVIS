"""
Byte-Pair Encoding (BPE) pre-tokenization and merge algorithms.

Handles lossless UTF-8 chunking and priority-ordered merge applications.
"""

from __future__ import annotations

import re
from typing import Dict, List, Sequence, Tuple
from myllm.tokenizer.vocabulary import BASE_VOCAB_SIZE, NUM_SPECIAL_TOKENS, byte_to_token_id


# Lossless pre-tokenization pattern matching contractions, words with optional space,
# punctuation runs, and whitespace sequences.
BPE_SPLIT_PATTERN = re.compile(
    r"'s|'t|'re|'ve|'m|'ll|'d| ?\w+| ?[^\s\w]+|\s+(?!\S)|\s+"
)


def split_text_into_chunks(text: str) -> List[str]:
    """
    Partition input text into pre-tokenized chunks losslessly.

    Guarantees: "".join(split_text_into_chunks(text)) == text for any input.
    """
    if not text:
        return []

    chunks = BPE_SPLIT_PATTERN.findall(text)

    # Absolute fallback to ensure lossless invariant under any exotic inputs
    if "".join(chunks) != text:
        return [text]

    return chunks


def chunk_to_byte_tokens(chunk: str) -> List[int]:
    """Convert a pre-tokenized string chunk into initial base byte token IDs (4-259)."""
    raw_bytes = chunk.encode("utf-8")
    return [byte_to_token_id(b) for b in raw_bytes]


def apply_bpe_merges_to_tokens(
    tokens: Sequence[int],
    merge_ranks: Dict[Tuple[int, int], int],
) -> List[int]:
    """
    Apply learned BPE merge rules to a sequence of token IDs according to priority rank.

    At each step, finds the adjacent pair present in merge_ranks with the lowest rank
    (earliest learned) and merges all non-overlapping occurrences left-to-right.

    Args:
        tokens: Initial sequence of token IDs.
        merge_ranks: Map from (token_a, token_b) to priority rank (0, 1, ...).

    Returns:
        New sequence of token IDs with all eligible merges applied.
    """
    if len(tokens) < 2:
        return list(tokens)

    current_tokens = list(tokens)

    while len(current_tokens) >= 2:
        # Find adjacent pair with the lowest rank (highest priority)
        min_rank: int | None = None
        best_pair: Tuple[int, int] | None = None

        for i in range(len(current_tokens) - 1):
            pair = (current_tokens[i], current_tokens[i + 1])
            rank = merge_ranks.get(pair)
            if rank is not None:
                if min_rank is None or rank < min_rank:
                    min_rank = rank
                    best_pair = pair

        # If no valid pair was found, merges are complete
        if min_rank is None or best_pair is None:
            break

        # Merge all occurrences of best_pair in the token sequence
        merged_token_id = BASE_VOCAB_SIZE + min_rank
        new_tokens: List[int] = []
        i = 0
        target_a, target_b = best_pair

        while i < len(current_tokens):
            if (
                i < len(current_tokens) - 1
                and current_tokens[i] == target_a
                and current_tokens[i + 1] == target_b
            ):
                new_tokens.append(merged_token_id)
                i += 2
            else:
                new_tokens.append(current_tokens[i])
                i += 1

        current_tokens = new_tokens

    return current_tokens
