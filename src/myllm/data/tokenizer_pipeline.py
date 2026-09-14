"""
Tokenizer integration and tokenization streaming for MyLLM dataset pipeline.

Utilizes the Phase 1 Byte-Level BPE Tokenizer, computes deterministic tokenizer
fingerprints, and processes document boundaries.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import List, Optional, Union
from myllm.tokenizer import Tokenizer


def compute_tokenizer_fingerprint(tokenizer: Tokenizer) -> str:
    """
    Compute a deterministic cryptographic SHA-256 fingerprint for a Tokenizer.

    Fingerprint covers vocabulary size, special token mapping, and canonical merge list.
    """
    canonical_repr = (
        f"vocab_size:{len(tokenizer)}|"
        f"special:{sorted(tokenizer.vocab.special_tokens.items())}|"
        f"merges:{tokenizer.vocab.merges_list}"
    )
    return hashlib.sha256(canonical_repr.encode("utf-8")).hexdigest()


class TokenizerPipeline:
    """
    Wraps the Phase 1 Tokenizer to provide document-level tokenization
    with boundary token control (BOS/EOS).
    """

    def __init__(self, tokenizer: Union[Tokenizer, str, Path]) -> None:
        if isinstance(tokenizer, (str, Path)):
            path = Path(tokenizer)
            if not path.is_file():
                raise FileNotFoundError(f"Tokenizer file not found at: {path}")
            self.tokenizer = Tokenizer.load(path)
        elif isinstance(tokenizer, Tokenizer):
            self.tokenizer = tokenizer
        else:
            raise TypeError(f"Expected Tokenizer instance or path, got {type(tokenizer)}")

        self.fingerprint = compute_tokenizer_fingerprint(self.tokenizer)
        self.vocab_size = len(self.tokenizer)

    def encode_document(
        self,
        text: str,
        add_bos: bool = False,
        add_eos: bool = True,
    ) -> List[int]:
        """
        Encode a document into a sequence of token IDs with document boundary tokens.

        Args:
            text: Input document text.
            add_bos: If True, prepend BOS token ID.
            add_eos: If True, append EOS token ID to demarcate document boundary.

        Returns:
            List of integer token IDs.
        """
        return self.tokenizer.encode(
            text=text,
            add_bos=add_bos,
            add_eos=add_eos,
        )
