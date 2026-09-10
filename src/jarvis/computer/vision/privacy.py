"""
Screen privacy policy and exclusion manager for JARVIS.
"""

from typing import List, Dict, Any, Optional
from jarvis.computer.vision.errors import ScreenPrivacyDeniedError


class ScreenPrivacyPolicy:
    """
    Manages privacy exclusions for screen capture and analysis.
    Blocks or redacts processing on password managers, banking, or private credential windows.
    """

    BLOCKED_WINDOW_KEYWORDS = [
        "password",
        "bitwarden",
        "1password",
        "keepass",
        "lastpass",
        "bank",
        "banking",
        "credential",
        "lock screen",
        "authenticator",
        "credit card",
    ]

    def __init__(self, blocked_keywords: Optional[List[str]] = None, enabled: bool = True):
        self.enabled = enabled
        self.blocked_keywords = blocked_keywords or self.BLOCKED_WINDOW_KEYWORDS

    def is_window_blocked(self, window_title: str) -> bool:
        """Checks if window_title matches any blocked privacy keyword."""
        if not self.enabled or not window_title:
            return False

        title_lower = window_title.lower()
        for kw in self.blocked_keywords:
            if kw in title_lower:
                return True
        return False

    def validate_screen_capture_allowed(self, window_title: str) -> None:
        """Raises ScreenPrivacyDeniedError if window capture is blocked."""
        if self.is_window_blocked(window_title):
            raise ScreenPrivacyDeniedError(
                f"SCREEN_PRIVACY_DENIED: Screen capture blocked for private/sensitive window '{window_title}'."
            )
