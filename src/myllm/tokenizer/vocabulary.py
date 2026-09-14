"""
Vocabulary definition and mapping for Byte-Level BPE.

Manages deterministic special tokens (0-3), base byte tokens (4-259),
and learned composite BPE merges (260+).
"""

from __future__ import annotations

from typing import Dict, List, Optional, Sequence, Tuple


# Standard Special Token Constants
PAD_TOKEN = "<PAD>"
UNK_TOKEN = "<UNK>"
BOS_TOKEN = "<BOS>"
EOS_TOKEN = "<EOS>"

PAD_ID = 0
UNK_ID = 1
BOS_ID = 2
EOS_ID = 3

SPECIAL_TOKENS_MAP: Dict[str, int] = {
    PAD_TOKEN: PAD_ID,
    UNK_TOKEN: UNK_ID,
    BOS_TOKEN: BOS_ID,
    EOS_TOKEN: EOS_ID,
}

SPECIAL_IDS_MAP: Dict[int, str] = {
    PAD_ID: PAD_TOKEN,
    UNK_ID: UNK_TOKEN,
    BOS_ID: BOS_TOKEN,
    EOS_ID: EOS_TOKEN,
}

NUM_SPECIAL_TOKENS = 4
NUM_BYTE_TOKENS = 256
BASE_VOCAB_SIZE = NUM_SPECIAL_TOKENS + NUM_BYTE_TOKENS  # 260


def byte_to_token_id(b: int) -> int:
    """Convert an integer byte value (0-255) to its deterministic base token ID (4-259)."""
    if not (0 <= b <= 255):
        raise ValueError(f"Byte value {b} must be between 0 and 255.")
    return b + NUM_SPECIAL_TOKENS


def token_id_to_byte(token_id: int) -> int:
    """Convert a base token ID (4-259) to its corresponding integer byte value (0-255)."""
    if not (NUM_SPECIAL_TOKENS <= token_id < BASE_VOCAB_SIZE):
        raise ValueError(f"Token ID {token_id} is not a single-byte token (4-259).")
    return token_id - NUM_SPECIAL_TOKENS


class Vocabulary:
    """
    Bi-directional, deterministic vocabulary for Byte-Level BPE.

    Token ID layout:
        0: <PAD>
        1: <UNK>
        2: <BOS>
        3: <EOS>
        4 .. 259: 256 individual byte values (0x00 .. 0xFF)
        260 .. N: Learned composite BPE merge tokens
    """

    def __init__(self) -> None:
        # Special tokens
        self._special_token_to_id: Dict[str, int] = dict(SPECIAL_TOKENS_MAP)
        self._id_to_special_token: Dict[int, str] = dict(SPECIAL_IDS_MAP)

        # Byte mappings for all non-special tokens (IDs >= 4)
        self._id_to_bytes: Dict[int, bytes] = {}
        self._bytes_to_id: Dict[bytes, int] = {}

        # Initialize base 256 byte tokens (IDs 4..259)
        for b in range(NUM_BYTE_TOKENS):
            tid = byte_to_token_id(b)
            raw_byte = bytes([b])
            self._id_to_bytes[tid] = raw_byte
            self._bytes_to_id[raw_byte] = tid

        # Merge rules: (token_id_a, token_id_b) -> merged_token_id
        self._merges: Dict[Tuple[int, int], int] = {}
        # Merge rank: (token_id_a, token_id_b) -> rank index (0, 1, 2, ...)
        self._merge_ranks: Dict[Tuple[int, int], int] = {}
        # Ordered list of merges: list of (token_id_a, token_id_b)
        self._merges_list: List[Tuple[int, int]] = []

    def __len__(self) -> int:
        """Total vocabulary size: 4 special tokens + 256 bytes + learned merges."""
        return BASE_VOCAB_SIZE + len(self._merges_list)

    @property
    def special_tokens(self) -> Dict[str, int]:
        return dict(self._special_token_to_id)

    @property
    def merges_list(self) -> List[Tuple[int, int]]:
        return list(self._merges_list)

    @property
    def merge_ranks(self) -> Dict[Tuple[int, int], int]:
        return dict(self._merge_ranks)

    def is_special_token_id(self, token_id: int) -> bool:
        """Check if token ID is a reserved special token (0-3)."""
        return token_id in self._id_to_special_token

    def is_special_token_str(self, token_str: str) -> bool:
        """Check if string matches a reserved special token."""
        return token_str in self._special_token_to_id

    def get_special_token_id(self, token_str: str) -> Optional[int]:
        return self._special_token_to_id.get(token_str)

    def get_special_token_str(self, token_id: int) -> Optional[str]:
        return self._id_to_special_token.get(token_id)

    def id_to_bytes(self, token_id: int) -> bytes:
        """
        Get the byte sequence corresponding to a non-special token ID.

        Raises:
            KeyError: If token_id is invalid.
            ValueError: If token_id is a special token.
        """
        if self.is_special_token_id(token_id):
            raise ValueError(
                f"Token ID {token_id} is a special token '{self._id_to_special_token[token_id]}' "
                f"and does not have a raw byte sequence."
            )
        if token_id not in self._id_to_bytes:
            raise KeyError(f"Token ID {token_id} not found in vocabulary (size {len(self)}).")
        return self._id_to_bytes[token_id]

    def bytes_to_id(self, b: bytes) -> Optional[int]:
        """Look up token ID for an exact byte sequence."""
        return self._bytes_to_id.get(b)

    def add_merge(self, token_a: int, token_b: int) -> int:
        """
        Add a learned BPE merge rule between token_a and token_b.

        Args:
            token_a: First token ID.
            token_b: Second token ID.

        Returns:
            The newly assigned composite token ID.

        Raises:
            ValueError: If either token is a special token, or if the pair is already merged.
        """
        pair = (token_a, token_b)
        if pair in self._merges:
            return self._merges[pair]

        if self.is_special_token_id(token_a) or self.is_special_token_id(token_b):
            raise ValueError(f"Cannot merge with special token IDs: {pair}")

        if token_a not in self._id_to_bytes or token_b not in self._id_to_bytes:
            raise KeyError(f"Both tokens {pair} must exist in vocabulary before merging.")

        new_id = BASE_VOCAB_SIZE + len(self._merges_list)
        merged_bytes = self._id_to_bytes[token_a] + self._id_to_bytes[token_b]

        rank = len(self._merges_list)
        self._merges[pair] = new_id
        self._merge_ranks[pair] = rank
        self._merges_list.append(pair)
        self._id_to_bytes[new_id] = merged_bytes
        self._bytes_to_id[merged_bytes] = new_id

        return new_id

    def get_merge_id(self, pair: Tuple[int, int]) -> Optional[int]:
        """Get the merged token ID for a pair, if it exists."""
        return self._merges.get(pair)

    def get_merge_rank(self, pair: Tuple[int, int]) -> Optional[int]:
        """Get the learned priority rank for a pair, if it exists."""
        return self._merge_ranks.get(pair)

    def contains_id(self, token_id: int) -> bool:
        """Check whether token_id is within the valid vocabulary range."""
        return 0 <= token_id < len(self)
