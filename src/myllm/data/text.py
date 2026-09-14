"""
Text normalization and safe Unicode validation for MyLLM dataset pipeline.

Conservative and non-destructive: preserves case, punctuation, internal whitespace,
and all Unicode characters.
"""

from __future__ import annotations

import unicodedata
from typing import Optional


def normalize_text(
    text: str,
    strip_bom: bool = True,
    normalize_newlines: bool = True,
    normalize_unicode: bool = False,
    unicode_form: str = "NFC",
    strip_outer_whitespace: bool = False,
) -> str:
    """
    Apply conservative text normalization.

    Args:
        text: Raw text string to normalize.
        strip_bom: If True, strip UTF-8 Byte Order Mark (BOM: '\\ufeff').
        normalize_newlines: If True, standardize '\\r\\n' and '\\r' to '\\n'.
        normalize_unicode: If True, apply unicodedata.normalize (default False).
        unicode_form: Form for Unicode normalization ('NFC', 'NFKC', etc.).
        strip_outer_whitespace: If True, strip leading/trailing whitespace.

    Returns:
        Cleaned text string preserving all case, punctuation, and internal whitespace.
    """
    if not text:
        return ""

    # 1. Strip UTF-8 BOM if present
    if strip_bom and text.startswith("\ufeff"):
        text = text[1:]

    # 2. Normalize carriage returns to standard Unix newlines
    if normalize_newlines:
        text = text.replace("\r\n", "\n").replace("\r", "\n")

    # 3. Optional Unicode normalization (disabled by default to preserve raw character bytes)
    if normalize_unicode:
        text = unicodedata.normalize(unicode_form, text)

    # 4. Optional outer whitespace stripping
    if strip_outer_whitespace:
        text = text.strip()

    return text


def is_valid_utf8_text(text: str) -> bool:
    """Validate that text is a valid string representable as UTF-8."""
    if not isinstance(text, str):
        return False
    try:
        text.encode("utf-8")
        return True
    except UnicodeEncodeError:
        return False
