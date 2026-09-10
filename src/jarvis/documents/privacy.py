"""
Document privacy filtering and redaction.
"""

import re
from typing import Dict, Any


class DocumentPrivacyManager:
    """
    Prevents leaking sensitive document text to persistent logs or memory stores.
    """

    REDACTION_PATTERNS = [
        (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[REDACTED_SSN]"),
        (re.compile(r"\b(?:\d[ -]*?){13,16}\b"), "[REDACTED_CARD]"),
        (re.compile(r"(?i)(api[_-]?key|secret|password|token)\s*[:=]\s*['\"]?[\w\-]{8,}['\"]?"), r"\1: [REDACTED_SECRET]"),
        (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"), "[REDACTED_EMAIL]"),
    ]

    def redact_sensitive_info(self, text: str) -> str:
        """Redacts common PII and secrets from text."""
        result = text
        for pattern, replacement in self.REDACTION_PATTERNS:
            result = pattern.sub(replacement, result)
        return result

    def format_log_snippet(self, text: str, max_length: int = 100) -> str:
        """Returns a safe, truncated log snippet with sensitive info redacted."""
        clean = self.redact_sensitive_info(text)
        if len(clean) > max_length:
            return clean[:max_length] + "..."
        return clean
