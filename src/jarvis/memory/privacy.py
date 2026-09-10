"""
Privacy and Security Policy Enforcement for JARVIS Memory Subsystem.
"""

import re
from typing import Optional
from jarvis.memory.errors import PrivacyViolationError
from jarvis.memory.models import PrivacyLevel, MemoryItem


class MemoryPrivacyPolicy:
    """Evaluates memory items to block sensitive credential persistence."""

    SENSITIVE_PATTERNS = [
        (r"(?i)password\s*[:=]\s*\S+", "password"),
        (r"(?i)passwd\s*[:=]\s*\S+", "password"),
        (r"(?i)api[_\-]?key\s*[:=]\s*\S+", "api_key"),
        (r"(?i)secret[_\-]?key\s*[:=]\s*\S+", "secret_key"),
        (r"(?i)access[_\-]?token\s*[:=]\s*\S+", "access_token"),
        (r"(?i)auth[_\-]?token\s*[:=]\s*\S+", "auth_token"),
        (r"(?i)bearer\s+[a-zA-Z0-9_\-\.=]+", "bearer_token"),
        (r"-----BEGIN\s+(?:RSA\s+)?PRIVATE\s+KEY-----", "private_key"),
        (r"\b4[0-9]{12}(?:[0-9]{3})?\b", "credit_card"),  # Visa
        (r"\b5[1-5][0-9]{14}\b", "credit_card"),          # Mastercard
        (r"\b\d{3}-\d{2}-\d{4}\b", "ssn"),                 # US SSN
    ]

    def validate(self, memory_item: MemoryItem) -> None:
        if memory_item.privacy_level == PrivacyLevel.SENSITIVE:
            raise PrivacyViolationError(
                "Memory item marked explicitly as SENSITIVE cannot be stored.",
                pattern_matched="privacy_level=SENSITIVE",
            )

        text_to_check = f"{memory_item.key} {memory_item.content} {memory_item.metadata}"
        for pattern, label in self.SENSITIVE_PATTERNS:
            if re.search(pattern, text_to_check):
                raise PrivacyViolationError(
                    f"Memory item rejected: content matches sensitive pattern '{label}'.",
                    pattern_matched=label,
                )

    def is_sensitive(self, text: str) -> bool:
        for pattern, _ in self.SENSITIVE_PATTERNS:
            if re.search(pattern, text):
                return True
        return False
