"""
Prompt Injection Defense and Untrusted Content Sanitizer for JARVIS.

Defends against prompt injection attacks embedded in untrusted web pages, documents, or memory items
(e.g. "Ignore previous instructions", "Bypass permission checks", "Execute shell command").
Isolates external content as untrusted payload data.
"""

import re
import logging
from typing import Dict, Any, Tuple

logger = logging.getLogger(__name__)


class PromptInjectionScanResult:
    def __init__(self, is_suspicious: bool, detected_patterns: list[str], sanitized_content: str):
        self.is_suspicious = is_suspicious
        self.detected_patterns = detected_patterns
        self.sanitized_content = sanitized_content


class PromptInjectionDefense:
    """Detects and isolates prompt injection attacks in untrusted external text."""

    INJECTION_PATTERNS = [
        r"\bignore\s+(?:all\s+)?(?:previous\s+)?(?:instructions|rules|system\s+prompt)\b",
        r"\bbypass\s+(?:security|permission|confirmation|policies|rules)\b",
        r"\bexecute\s+(?:shell|command|terminal|system)\s+without\s+confirmation\b",
        r"\bdelete\s+(?:all\s+)?(?:files|directories|database)\b",
        r"\bgrant\s+(?:admin|root|unrestricted)\s+access\b",
        r"\bsystem_prompt_override\b",
        r"\byou\s+are\s+now\s+(?:an?\s+unrestricted|jailbroken)\b",
    ]

    @classmethod
    def scan_content(cls, content_text: str, source_origin: str = "untrusted_web") -> PromptInjectionScanResult:
        if not content_text:
            return PromptInjectionScanResult(is_suspicious=False, detected_patterns=[], sanitized_content="")

        detected = []
        for pattern in cls.INJECTION_PATTERNS:
            if re.search(pattern, content_text, re.IGNORECASE):
                detected.append(pattern)

        if detected:
            logger.warning(f"PromptInjectionDefense detected {len(detected)} injection patterns in content from origin '{source_origin}'!")
            # Wrap content in untrusted payload demarcation tag to prevent instruction hijacking
            sanitized = f"[UNTRUSTED CONTENT PAYLOAD ({source_origin}): {content_text.strip()}]"
            return PromptInjectionScanResult(is_suspicious=True, detected_patterns=detected, sanitized_content=sanitized)

        return PromptInjectionScanResult(is_suspicious=False, detected_patterns=[], sanitized_content=content_text)
