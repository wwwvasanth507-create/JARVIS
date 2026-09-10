"""
Browser Element Interaction Module for JARVIS.
Handles clicking, filling form inputs, key presses, scrolling, and interaction verification.
"""

import time
import logging
from typing import Any, Dict, Optional

from jarvis.browser.session import BrowserSession
from jarvis.browser.selectors import SelectorEngine
from jarvis.browser.state import BrowserActionResult
from jarvis.browser.errors import TargetNotFoundError, AmbiguousTargetError

logger = logging.getLogger("jarvis.browser.interaction")


class BrowserInteraction:
    """Performs element clicks, form typing/filling, keyboard presses, and page scrolling."""

    def __init__(self, session: BrowserSession):
        self.session = session

    def click(self, target: Dict[str, Any] | str) -> BrowserActionResult:
        """Clicks target element resolved via SelectorEngine."""
        start_time = time.perf_counter()
        logger.info(f"CLICK_STARTED: Attempting click on {target}")
        try:
            page = self.session.get_active_page()
            loc, desc = SelectorEngine.resolve_locator(page, target)

            loc.click(timeout=5000)
            page.wait_for_load_state("domcontentloaded", timeout=5000)

            dur = time.perf_counter() - start_time
            logger.info(f"CLICK_COMPLETED: Clicked {desc} in {dur*1000:.2f} ms")

            return BrowserActionResult(
                success=True,
                status="SUCCESS",
                message=f"Clicked {desc}",
                data={"target": target, "description": desc},
                duration_seconds=round(dur, 4),
                verified=True,
            )
        except TargetNotFoundError as tne:
            return BrowserActionResult(success=False, status="FAILED", message=str(tne))
        except AmbiguousTargetError as ate:
            return BrowserActionResult(success=False, status="AMBIGUOUS_TARGET", message=str(ate))
        except Exception as e:
            logger.error(f"BROWSER_ERROR: Click failed for {target}: {e}")
            return BrowserActionResult(success=False, status="FAILED", message=f"Click failed: {e}")

    def fill(self, target: Dict[str, Any] | str, text: str) -> BrowserActionResult:
        """Fills form input field resolved via SelectorEngine."""
        start_time = time.perf_counter()
        logger.info(f"FORM_FILLED: Filling text into {target}")
        try:
            page = self.session.get_active_page()
            loc, desc = SelectorEngine.resolve_locator(page, target)

            loc.fill(text, timeout=5000)

            dur = time.perf_counter() - start_time
            return BrowserActionResult(
                success=True,
                status="SUCCESS",
                message=f"Filled text into {desc}",
                data={"target": target, "description": desc, "text_length": len(text)},
                duration_seconds=round(dur, 4),
                verified=True,
            )
        except Exception as e:
            return BrowserActionResult(success=False, status="FAILED", message=f"Fill failed: {e}")

    def type_text(self, target: Dict[str, Any] | str, text: str, delay_ms: int = 10) -> BrowserActionResult:
        """Types characters sequentially into target element."""
        start_time = time.perf_counter()
        try:
            page = self.session.get_active_page()
            loc, desc = SelectorEngine.resolve_locator(page, target)

            loc.type(text, delay=delay_ms, timeout=5000)

            dur = time.perf_counter() - start_time
            return BrowserActionResult(
                success=True,
                status="SUCCESS",
                message=f"Typed text into {desc}",
                duration_seconds=round(dur, 4),
                verified=True,
            )
        except Exception as e:
            return BrowserActionResult(success=False, status="FAILED", message=f"Type failed: {e}")

    def press(self, key: str, target: Optional[Dict[str, Any] | str] = None) -> BrowserActionResult:
        """Presses a single key (e.g. 'Enter', 'Tab', 'Escape') on active page or element."""
        start_time = time.perf_counter()
        try:
            page = self.session.get_active_page()
            if target:
                loc, desc = SelectorEngine.resolve_locator(page, target)
                loc.press(key, timeout=5000)
            else:
                page.keyboard.press(key)

            dur = time.perf_counter() - start_time
            return BrowserActionResult(
                success=True,
                status="SUCCESS",
                message=f"Pressed key '{key}'",
                duration_seconds=round(dur, 4),
                verified=True,
            )
        except Exception as e:
            return BrowserActionResult(success=False, status="FAILED", message=f"Key press failed: {e}")

    def scroll(
        self, direction: str = "down", amount: int = 300, target: Optional[Dict[str, Any] | str] = None
    ) -> BrowserActionResult:
        """Scrolls page or container element up/down."""
        start_time = time.perf_counter()
        try:
            page = self.session.get_active_page()
            delta_y = amount if direction.lower() == "down" else -amount

            if target:
                loc, _ = SelectorEngine.resolve_locator(page, target)
                loc.scroll_into_view_if_needed()
            else:
                page.mouse.wheel(0, delta_y)

            dur = time.perf_counter() - start_time
            return BrowserActionResult(
                success=True,
                status="SUCCESS",
                message=f"Scrolled {direction} by {amount}px",
                duration_seconds=round(dur, 4),
                verified=True,
            )
        except Exception as e:
            return BrowserActionResult(success=False, status="FAILED", message=f"Scroll failed: {e}")
