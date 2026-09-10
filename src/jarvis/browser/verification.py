"""
Browser Verification Module for JARVIS Automation.

Verifies post-action states (navigation, clicks, form fills, downloads) rather than
relying solely on missing Playwright exceptions.
"""

from dataclasses import dataclass
import logging
from pathlib import Path
from typing import Optional
from playwright.sync_api import Page

logger = logging.getLogger(__name__)


@dataclass
class VerificationResult:
    success: bool
    reason: str
    details: Optional[dict] = None


class BrowserVerification:
    """Provides explicit status verification after browser operations."""

    @staticmethod
    def verify_navigation(
        page: Page,
        expected_url_substring: Optional[str] = None,
        expected_title_substring: Optional[str] = None,
    ) -> VerificationResult:
        """Verifies that navigation produced a valid, active page."""
        current_url = page.url
        current_title = page.title()

        if current_url in ("about:blank", "", "data:,"):
            return VerificationResult(
                success=False,
                reason="Page is empty or about:blank",
                details={"url": current_url, "title": current_title},
            )

        if expected_url_substring and expected_url_substring.lower() not in current_url.lower():
            return VerificationResult(
                success=False,
                reason=f"Expected URL containing '{expected_url_substring}', got '{current_url}'",
                details={"url": current_url, "title": current_title},
            )

        if expected_title_substring and expected_title_substring.lower() not in current_title.lower():
            return VerificationResult(
                success=False,
                reason=f"Expected title containing '{expected_title_substring}', got '{current_title}'",
                details={"url": current_url, "title": current_title},
            )

        return VerificationResult(
            success=True,
            reason="Navigation verified successfully",
            details={"url": current_url, "title": current_title},
        )

    @staticmethod
    def verify_element_visible(
        page: Page,
        selector: str,
        timeout_ms: float = 2000.0,
    ) -> VerificationResult:
        """Verifies that a specific element selector is visible in the viewport."""
        try:
            is_vis = page.is_visible(selector, timeout=timeout_ms)
            if is_vis:
                return VerificationResult(
                    success=True,
                    reason=f"Element '{selector}' is visible",
                )
            return VerificationResult(
                success=False,
                reason=f"Element '{selector}' exists but is not visible",
            )
        except Exception as e:
            return VerificationResult(
                success=False,
                reason=f"Element '{selector}' not found: {e}",
            )

    @staticmethod
    def verify_text_present(
        page: Page,
        text: str,
    ) -> VerificationResult:
        """Verifies that text snippet is present in the visible page content."""
        body_text = page.inner_text("body")
        if text.lower() in body_text.lower():
            return VerificationResult(
                success=True,
                reason=f"Text '{text}' found in page body",
            )
        return VerificationResult(
            success=False,
            reason=f"Text '{text}' not found in page body",
        )

    @staticmethod
    def verify_download(save_path: str, min_bytes: int = 1) -> VerificationResult:
        """Verifies downloaded file exists and meets minimum size requirement."""
        path = Path(save_path)
        if not path.exists():
            return VerificationResult(
                success=False,
                reason=f"Downloaded file does not exist: {save_path}",
            )
        size = path.stat().st_size
        if size < min_bytes:
            return VerificationResult(
                success=False,
                reason=f"Downloaded file size ({size} bytes) below minimum threshold ({min_bytes} bytes)",
                details={"size_bytes": size},
            )
        return VerificationResult(
            success=True,
            reason="Download verified successfully",
            details={"path": str(path), "size_bytes": size},
        )
