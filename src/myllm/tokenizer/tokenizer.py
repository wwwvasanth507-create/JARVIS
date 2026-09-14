"""
Main Byte-Level BPE Tokenizer class for MyLLM.

Provides production-ready encoding, decoding, training, and serialization.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Union
from myllm.tokenizer.bpe import (
    apply_bpe_merges_to_tokens,
    chunk_to_byte_tokens,
    split_text_into_chunks,
)
from myllm.tokenizer.serialization import load_tokenizer_json, save_tokenizer_json
from myllm.tokenizer.trainer import BPETrainer
from myllm.tokenizer.vocabulary import (
    BASE_VOCAB_SIZE,
    BOS_ID,
    BOS_TOKEN,
    EOS_ID,
    EOS_TOKEN,
    PAD_ID,
    PAD_TOKEN,
    UNK_ID,
    UNK_TOKEN,
    Vocabulary,
)


class Tokenizer:
    """
    Byte-Level BPE Tokenizer for MyLLM.

    Encodes arbitrary UTF-8 text into deterministic token IDs and reconstructs
    text losslessly via byte-level representations.
    """

    def __init__(
        self,
        vocabulary: Optional[Vocabulary] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.vocab = vocabulary if vocabulary is not None else Vocabulary()
        self.config = config or {}

    def __len__(self) -> int:
        return len(self.vocab)

    @property
    def vocab_size(self) -> int:
        return len(self.vocab)

    # Special token ID accessors
    @property
    def pad_token_id(self) -> int:
        return PAD_ID

    @property
    def unk_token_id(self) -> int:
        return UNK_ID

    @property
    def bos_token_id(self) -> int:
        return BOS_ID

    @property
    def eos_token_id(self) -> int:
        return EOS_ID

    # Special token string accessors
    @property
    def pad_token(self) -> str:
        return PAD_TOKEN

    @property
    def unk_token(self) -> str:
        return UNK_TOKEN

    @property
    def bos_token(self) -> str:
        return BOS_TOKEN

    @property
    def eos_token(self) -> str:
        return EOS_TOKEN

    def encode(
        self,
        text: str,
        add_bos: bool = False,
        add_eos: bool = False,
        max_length: Optional[int] = None,
        truncation: bool = False,
    ) -> List[int]:
        """
        Encode input text into a sequence of token IDs.

        Pipeline:
            text -> UTF-8 chunks -> initial byte tokens (4-259) ->
            priority-ordered BPE merges -> token IDs.

        Args:
            text: String input to tokenize.
            add_bos: If True, prepend BOS_ID (2).
            add_eos: If True, append EOS_ID (3).
            max_length: Optional sequence length cap.
            truncation: If True and max_length is set, truncate token sequence.

        Returns:
            List of integer token IDs.
        """
        if not isinstance(text, str):
            raise TypeError(f"Input text must be a str, got {type(text).__name__}.")

        chunks = split_text_into_chunks(text)
        merge_ranks = self.vocab.merge_ranks
        token_ids: List[int] = []

        for chunk in chunks:
            initial_tokens = chunk_to_byte_tokens(chunk)
            merged_tokens = apply_bpe_merges_to_tokens(initial_tokens, merge_ranks)
            token_ids.extend(merged_tokens)

        if add_bos:
            token_ids.insert(0, self.bos_token_id)
        if add_eos:
            token_ids.append(self.eos_token_id)

        if max_length is not None and truncation and len(token_ids) > max_length:
            token_ids = token_ids[:max_length]

        return token_ids

    def decode(
        self,
        token_ids: Sequence[int],
        skip_special_tokens: bool = False,
    ) -> str:
        """
        Decode a sequence of token IDs back into text.

        Args:
            token_ids: Sequence of token IDs to decode.
            skip_special_tokens: If True, omit special tokens (<PAD>, <UNK>, <BOS>, <EOS>).
                                 If False, special tokens are represented by their string names.

        Returns:
            Decoded UTF-8 text string.

        Raises:
            ValueError: If any token ID is outside the valid vocabulary range.
        """
        byte_segments: List[bytes] = []

        for token_id in token_ids:
            if not self.vocab.contains_id(token_id):
                raise ValueError(
                    f"Invalid token ID {token_id}. Valid vocabulary range is 0 to {len(self.vocab) - 1}."
                )

            if self.vocab.is_special_token_id(token_id):
                if skip_special_tokens:
                    continue
                # Represent special token by its name encoded in UTF-8
                name = self.vocab.get_special_token_str(token_id) or ""
                byte_segments.append(name.encode("utf-8"))
            else:
                byte_segments.append(self.vocab.id_to_bytes(token_id))

        raw_bytes = b"".join(byte_segments)
        return raw_bytes.decode("utf-8", errors="replace")

    def save(self, file_path: Union[str, Path]) -> Path:
        """Serialize tokenizer vocabulary, merges, and config to a JSON file."""
        return save_tokenizer_json(self.vocab, file_path, config=self.config)

    @classmethod
    def load(cls, file_path: Union[str, Path]) -> Tokenizer:
        """Load tokenizer from a serialized JSON file."""
        vocab, config = load_tokenizer_json(file_path)
        return cls(vocabulary=vocab, config=config)

    @classmethod
    def train(
        cls,
        corpus: Iterable[str],
        vocab_size: int = 1000,
        min_pair_frequency: int = 2,
        max_documents: Optional[int] = None,
        max_training_bytes: Optional[int] = None,
    ) -> Tokenizer:
        """
        Train a new Tokenizer on a text corpus from scratch.

        Args:
            corpus: Iterable of text strings.
            vocab_size: Target vocabulary size (>= 260).
            min_pair_frequency: Minimum pair frequency required to merge.
            max_documents: Optional limit on documents to ingest.
            max_training_bytes: Optional limit on UTF-8 bytes to ingest.

        Returns:
            A newly trained Tokenizer instance.
        """
        trainer = BPETrainer(
            vocab_size=vocab_size,
            min_pair_frequency=min_pair_frequency,
            max_documents=max_documents,
            max_training_bytes=max_training_bytes,
        )
        vocab, _ = trainer.train(corpus)
        config = {
            "vocab_size": vocab_size,
            "min_pair_frequency": min_pair_frequency,
            "max_documents": max_documents,
            "max_training_bytes": max_training_bytes,
        }
        return cls(vocabulary=vocab, config=config)
