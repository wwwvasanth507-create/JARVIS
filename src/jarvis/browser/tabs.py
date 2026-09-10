"""
Browser Tab Management Module for JARVIS.
Handles opening new tabs, listing open tabs, switching active tab focus, and closing tabs.
"""

import time
import logging
from typing import List, Optional

from jarvis.browser.session import BrowserSession
from jarvis.browser.state import BrowserActionResult, TabInfo

logger = logging.getLogger("jarvis.browser.tabs")


class BrowserTabs:
    """Manages browser tabs and page context switching."""

    def __init__(self, session: BrowserSession):
        self.session = session

    def list_tabs(self) -> List[TabInfo]:
        """Returns structured metadata for all open tabs in current browser context."""
        context = self.session.get_context()
        active_page = self.session.get_active_page()
        pages = context.pages

        tabs: List[TabInfo] = []
        for idx, page in enumerate(pages):
            is_active = (page == active_page)
            tabs.append(
                TabInfo(
                    id=str(idx),
                    url=page.url if not page.is_closed() else "",
                    title=page.title() if not page.is_closed() else "",
                    is_active=is_active,
                )
            )
        return tabs

    def new_tab(self, url: Optional[str] = None) -> BrowserActionResult:
        """Opens a new browser tab and optionally navigates to URL."""
        start_time = time.perf_counter()
        logger.info("TAB_CREATED: Opening new browser tab")
        try:
            context = self.session.get_context()
            new_page = context.new_page()
            self.session._active_page = new_page

            if url:
                from jarvis.browser.navigation import BrowserNavigation
                nav = BrowserNavigation(self.session)
                nav.goto(url)

            dur = time.perf_counter() - start_time
            tabs = self.list_tabs()
            return BrowserActionResult(
                success=True,
                status="SUCCESS",
                message=f"Opened new tab ({new_page.title()})",
                data={"tab_id": str(len(tabs) - 1), "url": new_page.url, "title": new_page.title()},
                duration_seconds=round(dur, 4),
                verified=True,
            )
        except Exception as e:
            logger.error(f"BROWSER_ERROR: Failed to open new tab: {e}")
            return BrowserActionResult(success=False, status="FAILED", message=f"Failed to open new tab: {e}")

    def switch_tab(self, tab_id_or_index: int | str) -> BrowserActionResult:
        """Switches active page focus to specified tab index or ID."""
        start_time = time.perf_counter()
        try:
            context = self.session.get_context()
            pages = context.pages
            idx = int(tab_id_or_index)

            if not (0 <= idx < len(pages)):
                return BrowserActionResult(
                    success=False,
                    status="FAILED",
                    message=f"Tab index {idx} out of bounds (Total tabs: {len(pages)})",
                )

            target_page = pages[idx]
            target_page.bring_to_front()
            self.session._active_page = target_page

            dur = time.perf_counter() - start_time
            logger.info(f"TAB_SWITCHED: Switched to tab {idx} ('{target_page.title()}')")

            return BrowserActionResult(
                success=True,
                status="SUCCESS",
                message=f"Switched to tab {idx} ('{target_page.title()}')",
                data={"tab_id": str(idx), "url": target_page.url, "title": target_page.title()},
                duration_seconds=round(dur, 4),
                verified=True,
            )
        except Exception as e:
            return BrowserActionResult(success=False, status="FAILED", message=f"Failed to switch tab: {e}")

    def close_tab(self, tab_id_or_index: Optional[int | str] = None) -> BrowserActionResult:
        """Closes target tab (or active tab if unspecified)."""
        start_time = time.perf_counter()
        try:
            context = self.session.get_context()
            pages = context.pages
            if not pages:
                return BrowserActionResult(success=True, status="SUCCESS", message="No open tabs to close")

            if tab_id_or_index is not None:
                idx = int(tab_id_or_index)
                if not (0 <= idx < len(pages)):
                    return BrowserActionResult(success=False, status="FAILED", message=f"Tab index {idx} invalid")
                target_page = pages[idx]
            else:
                target_page = self.session.get_active_page()

            target_title = target_page.title()
            target_page.close()

            # Update active page pointer
            remaining_pages = context.pages
            if remaining_pages:
                self.session._active_page = remaining_pages[-1]
            else:
                self.session._active_page = context.new_page()

            dur = time.perf_counter() - start_time
            return BrowserActionResult(
                success=True,
                status="SUCCESS",
                message=f"Closed tab ('{target_title}')",
                duration_seconds=round(dur, 4),
                verified=True,
            )
        except Exception as e:
            return BrowserActionResult(success=False, status="FAILED", message=f"Failed to close tab: {e}")
