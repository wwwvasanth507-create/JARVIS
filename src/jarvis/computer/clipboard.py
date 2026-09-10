"""
Controlled System Clipboard Controller for JARVIS.

Provides safe clipboard read, write, clear, and credential detection with zero background continuous logging.
"""

import re
import subprocess
import platform
import logging
from typing import Dict, Any, Tuple

logger = logging.getLogger(__name__)


class ClipboardController:
    """Manages OS clipboard interactions with privacy safeguards."""

    CREDENTIAL_PATTERNS = [
        r"\b(?:password|passwd|secret|api[_-]?key|bearer\s+[a-z0-9\.\-_]+|token)\b",
        r"\b[A-Za-z0-9+/]{32,}={0,2}\b",  # Base64 tokens
        r"\b[0-9a-fA-F]{32,}\b",         # Hex keys
    ]

    @classmethod
    def get_text(cls) -> str:
        """Reads current clipboard text safely using OS primitives."""
        try:
            if platform.system() == "Windows":
                cmd = ["powershell", "-NoProfile", "-Command", "Get-Clipboard"]
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=3)
                if res.returncode == 0:
                    return res.stdout.rstrip("\r\n")
            elif platform.system() == "Darwin":
                res = subprocess.run(["pbpaste"], capture_output=True, text=True, timeout=3)
                if res.returncode == 0:
                    return res.stdout
            else:
                res = subprocess.run(["xclip", "-selection", "clipboard", "-o"], capture_output=True, text=True, timeout=3)
                if res.returncode == 0:
                    return res.stdout
        except Exception as e:
            logger.warning(f"Error reading clipboard: {e}")
        return ""

    @classmethod
    def set_text(cls, text: str) -> bool:
        """Sets clipboard text using OS primitives."""
        try:
            if platform.system() == "Windows":
                cmd = ["powershell", "-NoProfile", "-Command", "Set-Clipboard -Value $input"]
                res = subprocess.run(cmd, input=text, capture_output=True, text=True, timeout=3)
                return res.returncode == 0
            elif platform.system() == "Darwin":
                res = subprocess.run(["pbcopy"], input=text, capture_output=True, text=True, timeout=3)
                return res.returncode == 0
            else:
                res = subprocess.run(["xclip", "-selection", "clipboard"], input=text, capture_output=True, text=True, timeout=3)
                return res.returncode == 0
        except Exception as e:
            logger.warning(f"Error setting clipboard: {e}")
            return False

    @classmethod
    def clear(cls) -> bool:
        """Clears clipboard contents."""
        return cls.set_text("")

    @classmethod
    def inspect(cls) -> Dict[str, Any]:
        """Inspects clipboard metadata and credential patterns without logging full content."""
        text = cls.get_text()
        has_credentials = False
        for pat in cls.CREDENTIAL_PATTERNS:
            if re.search(pat, text, re.IGNORECASE):
                has_credentials = True
                break

        return {
            "length": len(text),
            "is_empty": len(text) == 0,
            "contains_potential_credential": has_credentials,
            "preview": text[:20] + "..." if len(text) > 20 and not has_credentials else ("[REDACTED]" if has_credentials else text)
        }
