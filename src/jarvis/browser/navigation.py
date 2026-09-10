"""
Browser Navigation Module for JARVIS.
Handles URL validation, page navigation, history traversal (back/forward), and page reload.
"""

from urllib.parse import urlparse
import time
import logging
from typing import List, Optional

from jarvis.browser.session import BrowserSession
from jarvis.browser.state import BrowserActionResult
from jarvis.browser.errors import NavigationError, SecurityViolationError

logger = logging.getLogger("jarvis.browser.navigation")


def validate_url(url: str, allowed_schemes: Optional[List[str]] = None) -> str:
    """Standalone module helper to validate URL scheme and formatting."""
    nav = BrowserNavigation(session=None, allowed_schemes=allowed_schemes)
    return nav.validate_url(url)


class BrowserNavigation:
    """Handles browser URL navigation, URL safety validation, and history management."""

    def __init__(self, session: BrowserSession, allowed_schemes: Optional[List[str]] = None):
        self.session = session
        self.allowed_schemes = allowed_schemes or ["http", "https", "file"]

    def validate_url(self, url: str) -> str:
        """Validates URL scheme and returns normalized URL string."""
        if not url:
            raise NavigationError("URL parameter cannot be empty.")

        clean_url = url.strip()
        if clean_url.startswith(("javascript:", "data:", "custom:")):
            scheme = clean_url.split(":")[0]
            raise SecurityViolationError(
                f"URL scheme '{scheme}' is disallowed by security policy. Allowed schemes: {self.allowed_schemes}"
            )

        if not clean_url.startswith(("http://", "https://", "file://")):
            if clean_url.startswith("file:/"):
                clean_url = f"file:///{clean_url[6:].lstrip('/')}"
            else:
                clean_url = f"https://{clean_url}"

        parsed = urlparse(clean_url)
        if parsed.scheme.lower() not in self.allowed_schemes:
            raise SecurityViolationError(
                f"URL scheme '{parsed.scheme}' is disallowed by security policy. Allowed schemes: {self.allowed_schemes}"
            )

        return clean_url


    def goto(self, url: str, wait_until: str = "domcontentloaded") -> BrowserActionResult:
        """Navigates current page to validated target URL."""
        start_time = time.perf_counter()
        logger.info(f"NAVIGATION_STARTED: Navigating to '{url}'")

        try:
            target_url = self.validate_url(url)
            page = self.session.get_active_page()

            response = page.goto(target_url, wait_until=wait_until)
            page.wait_for_load_state("domcontentloaded")

            dur = time.perf_counter() - start_time
            current_url = page.url
            current_title = page.title()
            logger.info(f"NAVIGATION_COMPLETED: Loaded '{current_title}' ({current_url}) in {dur*1000:.2f} ms")

            return BrowserActionResult(
                success=True,
                status="SUCCESS",
                message=f"Navigated to '{current_title}'",
                data={
                    "url": current_url,
                    "title": current_title,
                    "status_code": response.status if response else 200,
                },
                duration_seconds=round(dur, 4),
                verified=True,
            )
        except SecurityViolationError as se:
            logger.error(f"BROWSER_ERROR: Security violation: {se}")
            return BrowserActionResult(
                success=False,
                status="DENIED",
                message=str(se),
                duration_seconds=round(time.perf_counter() - start_time, 4),
            )
        except Exception as e:
            logger.error(f"BROWSER_ERROR: Navigation failed for '{url}': {e}")
            return BrowserActionResult(
                success=False,
                status="FAILED",
                message=f"Navigation failed: {str(e)}",
                duration_seconds=round(time.perf_counter() - start_time, 4),
            )

    def back(self) -> BrowserActionResult:
        """Goes back to previous page in history."""
        start_time = time.perf_counter()
        try:
            page = self.session.get_active_page()
            response = page.go_back()
            dur = time.perf_counter() - start_time
            return BrowserActionResult(
                success=True,
                status="SUCCESS",
                message="Navigated back",
                data={"url": page.url, "title": page.title()},
                duration_seconds=round(dur, 4),
                verified=True,
            )
        except Exception as e:
            return BrowserActionResult(success=False, status="FAILED", message=f"Back navigation failed: {e}")

    def forward(self) -> BrowserActionResult:
        """Goes forward to next page in history."""
        start_time = time.perf_counter()
        try:
            page = self.session.get_active_page()
            response = page.go_forward()
            dur = time.perf_counter() - start_time
            return BrowserActionResult(
                success=True,
                status="SUCCESS",
                message="Navigated forward",
                data={"url": page.url, "title": page.title()},
                duration_seconds=round(dur, 4),
                verified=True,
            )
        except Exception as e:
            return BrowserActionResult(success=False, status="FAILED", message=f"Forward navigation failed: {e}")

    def reload(self) -> BrowserActionResult:
        """Reloads current page."""
        start_time = time.perf_counter()
        try:
            page = self.session.get_active_page()
            response = page.reload()
            dur = time.perf_counter() - start_time
            return BrowserActionResult(
                success=True,
                status="SUCCESS",
                message="Reloaded page",
                data={"url": page.url, "title": page.title()},
                duration_seconds=round(dur, 4),
                verified=True,
            )
        except Exception as e:
            return BrowserActionResult(success=False, status="FAILED", message=f"Page reload failed: {e}")
