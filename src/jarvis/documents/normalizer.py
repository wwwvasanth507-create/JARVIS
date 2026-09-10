"""
Text normalization for extracted document content.
"""

import re


class DocumentNormalizer:
    """
    Normalizes whitespace, line endings, and malformed characters while preserving document structure.
    Does NOT alter source files on disk.
    """

    def normalize(self, text: str) -> str:
        if not text:
            return ""

        # Normalize line endings
        normalized = text.replace("\r\n", "\n").replace("\r", "\n")

        # Replace non-breaking spaces and zero-width spaces
        normalized = normalized.replace("\u00a0", " ").replace("\u200b", "")

        # Collapse excess trailing spaces per line
        lines = [re.sub(r"[ \t]+$", "", line) for line in normalized.split("\n")]
        normalized = "\n".join(lines)

        # Collapse excess blank lines (max 2 consecutive newlines)
        normalized = re.sub(r"\n{3,}", "\n\n", normalized)

        return normalized.strip()
