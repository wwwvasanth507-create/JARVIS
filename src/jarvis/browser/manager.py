"""
Unified Browser Manager for JARVIS Automation Engine.

Orchestrates browser process lifecycle, persistent context reuse, navigation,
tab management, element interaction, structured extraction, form filling,
download/upload security, post-action verification, and observability logging.
"""

from dataclasses import asdict
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

from jarvis.core.config import get_settings, BrowserSettings
from jarvis.browser.errors import (
    BrowserError, CaptchaDetectedError, SecurityViolationError,
    TargetNotFoundError, AmbiguousTargetError, NavigationError
)
from jarvis.browser.state import BrowserState, TabInfo, BrowserActionResult, SearchResult
from jarvis.browser.session import BrowserSession
from jarvis.browser.navigation import BrowserNavigation
from jarvis.browser.tabs import BrowserTabs
from jarvis.browser.selectors import SelectorEngine
from jarvis.browser.interaction import BrowserInteraction
from jarvis.browser.extraction import BrowserExtraction
from jarvis.browser.downloads import BrowserDownloads, DownloadRecord
from jarvis.browser.uploads import BrowserUploads
from jarvis.browser.forms import BrowserForms
from jarvis.browser.verification import BrowserVerification, VerificationResult

logger = logging.getLogger("jarvis.browser.manager")

# Common CAPTCHA and anti-bot challenge indicators
CAPTCHA_SIGNATURES = [
    "g-recaptcha", "h-captcha", "cf-turnstile", "cf-challenge",
    "captcha", "bot protection", "verify you are human", "please verify you are a human"
]


class BrowserManager:
    """Central manager for JARVIS browser automation operations."""

    def __init__(self, settings: Optional[BrowserSettings] = None) -> None:
        self.settings = settings or get_settings().browser
        self.session = BrowserSession(settings=self.settings)
        self.navigation = BrowserNavigation(self.session, allowed_schemes=self.settings.allowed_schemes)
        self.tabs = BrowserTabs(self.session)
        self.selector_engine = SelectorEngine()
        self.interaction = BrowserInteraction(self.session)
        self.extraction = BrowserExtraction(self.session)
        self.downloads = BrowserDownloads(download_dir=self.settings.download_dir)
        self.uploads = BrowserUploads(selector_engine=self.selector_engine)
        self.forms = BrowserForms(selector_engine=self.selector_engine)

    # -------------------------------------------------------------------------
    # Lifecycle & Health
    # -------------------------------------------------------------------------

    def start(self) -> None:
        """Explicitly starts the browser session process."""
        self.session.start()
        logger.info("EVENT: BROWSER_STARTED")

    def stop(self) -> None:
        """Stops the browser session process and frees resources."""
        self.session.stop()
        logger.info("EVENT: BROWSER_STOPPED")

    def restart(self) -> None:
        """Restarts the browser session."""
        self.stop()
        self.start()

    def is_running(self) -> bool:
        """Returns True if the browser session process is active."""
        return self.session.is_running

    def get_state(self) -> BrowserState:
        """Retrieves structured, lightweight state metadata for the browser subsystem."""
        if not self.is_running():
            return BrowserState(running=False)

        tabs = self.tabs.list_tabs()
        page = self.session.get_active_page()
        active_tab_idx = self.session.get_active_tab_index()

        url = page.url if page else ""
        title = page.title() if page else ""

        return BrowserState(
            running=True,
            current_url=url,
            current_title=title,
            active_tab_id=str(active_tab_idx),
            tabs=tabs,
        )

    # -------------------------------------------------------------------------
    # Navigation & Tab Management
    # -------------------------------------------------------------------------

    def open(self, url: str) -> BrowserActionResult:
        """Opens a URL (alias for goto with verification & CAPTCHA detection)."""
        return self.goto(url)

    def goto(self, url: str) -> BrowserActionResult:
        """Navigates active tab to a URL with verification."""
        logger.info("EVENT: NAVIGATION_STARTED | Target: %s", url)
        try:
            nav_res = self.navigation.goto(url)
            if not nav_res.success:
                return nav_res
            page = self.session.get_active_page()
            self._check_captcha(page)
            ver = BrowserVerification.verify_navigation(page, expected_url_substring=url.split("//")[-1].split("/")[0])
            logger.info("EVENT: NAVIGATION_COMPLETED | URL: %s | Title: %s", page.url, page.title())
            return BrowserActionResult(
                success=ver.success,
                action="goto",
                url=page.url,
                title=page.title(),
                message=ver.reason,
            )
        except CaptchaDetectedError as ce:
            logger.warning("EVENT: BROWSER_ERROR | Captcha Detected: %s", ce)
            return BrowserActionResult(
                success=False,
                action="goto",
                url=url,
                message="HUMAN_INTERVENTION_REQUIRED",
                error=str(ce),
            )
        except Exception as e:
            logger.error("EVENT: BROWSER_ERROR | Navigation Failed: %s", e)
            return BrowserActionResult(
                success=False,
                action="goto",
                url=url,
                message="Navigation failed",
                error=str(e),
            )

    def back(self) -> BrowserActionResult:
        return self.navigation.back()

    def forward(self) -> BrowserActionResult:
        return self.navigation.forward()

    def reload(self) -> BrowserActionResult:
        return self.navigation.reload()

    def list_tabs(self) -> List[TabInfo]:
        return self.tabs.list_tabs()

    def new_tab(self, url: Optional[str] = None) -> BrowserActionResult:
        res = self.tabs.new_tab(url)
        logger.info("EVENT: TAB_CREATED")
        return res

    def switch_tab(self, index: int) -> BrowserActionResult:
        res = self.tabs.switch_tab(index)
        logger.info("EVENT: TAB_SWITCHED | Tab Index: %d", index)
        return res

    def close_tab(self, index: Optional[int] = None) -> BrowserActionResult:
        return self.tabs.close_tab(index)

    # -------------------------------------------------------------------------
    # Content Reading & Web Search
    # -------------------------------------------------------------------------

    def read_page(self, max_chars: Optional[int] = None) -> Dict[str, Any]:
        """Extracts structured readable content from the active page."""
        return self.extraction.read_page(max_chars=max_chars)

    def search(self, query: str, num_results: int = 5) -> List[SearchResult]:
        """Performs a web search via the browser without external search APIs."""
        return self.extraction.search(query=query, num_results=num_results)

    # -------------------------------------------------------------------------
    # Interaction (Clicking, Typing, Filling, Pressing, Scrolling)
    # -------------------------------------------------------------------------

    def click(self, target: Union[str, dict], timeout_ms: Optional[float] = None) -> BrowserActionResult:
        logger.info("EVENT: CLICK_STARTED | Target: %s", target)
        try:
            page = self.session.get_active_page()
            self.interaction.click(target, timeout_ms=timeout_ms)
            self._check_captcha(page)
            logger.info("EVENT: CLICK_COMPLETED | URL: %s", page.url)
            return BrowserActionResult(
                success=True,
                action="click",
                url=page.url,
                title=page.title(),
                message="Click completed successfully",
            )
        except CaptchaDetectedError as ce:
            return BrowserActionResult(
                success=False,
                action="click",
                message="HUMAN_INTERVENTION_REQUIRED",
                error=str(ce),
            )
        except Exception as e:
            logger.error("EVENT: BROWSER_ERROR | Click failed: %s", e)
            return BrowserActionResult(
                success=False,
                action="click",
                message="Click operation failed",
                error=str(e),
            )

    def fill(self, target: Union[str, dict], text: str, timeout_ms: Optional[float] = None) -> BrowserActionResult:
        try:
            page = self.session.get_active_page()
            self.interaction.fill(target, text, timeout_ms=timeout_ms)
            logger.info("EVENT: FORM_FILLED | Target: %s", target)
            return BrowserActionResult(
                success=True,
                action="fill",
                url=page.url,
                title=page.title(),
                message=f"Filled element with text",
            )
        except Exception as e:
            logger.error("EVENT: BROWSER_ERROR | Fill failed: %s", e)
            return BrowserActionResult(
                success=False,
                action="fill",
                message="Fill operation failed",
                error=str(e),
            )

    def type_text(self, target: Union[str, dict], text: str, delay_ms: float = 20.0) -> BrowserActionResult:
        try:
            page = self.session.get_active_page()
            self.interaction.type_text(target, text, delay_ms=delay_ms)
            return BrowserActionResult(
                success=True,
                action="type",
                url=page.url,
                title=page.title(),
            )
        except Exception as e:
            return BrowserActionResult(
                success=False,
                action="type",
                error=str(e),
            )

    def press(self, key: str) -> BrowserActionResult:
        try:
            page = self.session.get_active_page()
            self.interaction.press(key)
            return BrowserActionResult(
                success=True,
                action="press",
                url=page.url,
                title=page.title(),
            )
        except Exception as e:
            return BrowserActionResult(
                success=False,
                action="press",
                error=str(e),
            )

    def scroll(self, direction: str = "down", amount: int = 500) -> BrowserActionResult:
        try:
            page = self.session.get_active_page()
            self.interaction.scroll(direction=direction, amount=amount)
            return BrowserActionResult(
                success=True,
                action="scroll",
                url=page.url,
                title=page.title(),
            )
        except Exception as e:
            return BrowserActionResult(
                success=False,
                action="scroll",
                error=str(e),
            )

    # -------------------------------------------------------------------------
    # Downloads, Uploads, Forms
    # -------------------------------------------------------------------------

    def download(self, target: Union[str, dict], timeout_ms: float = 30000.0) -> BrowserActionResult:
        logger.info("EVENT: DOWNLOAD_STARTED | Target: %s", target)
        try:
            page = self.session.get_active_page()
            def trigger():
                self.interaction.click(target, timeout_ms=timeout_ms)

            record: DownloadRecord = self.downloads.download_file(page, trigger, timeout_ms=timeout_ms)
            ver = BrowserVerification.verify_download(record.save_path)
            logger.info("EVENT: DOWNLOAD_COMPLETED | File: %s | Size: %d", record.filename, record.size_bytes)
            return BrowserActionResult(
                success=ver.success,
                action="download",
                url=page.url,
                title=page.title(),
                message=ver.reason,
                details=asdict(record),
            )
        except Exception as e:
            logger.error("EVENT: BROWSER_ERROR | Download failed: %s", e)
            return BrowserActionResult(
                success=False,
                action="download",
                error=str(e),
            )

    def upload(self, target: Union[str, dict], file_paths: Union[str, Path, List[Union[str, Path]]]) -> BrowserActionResult:
        try:
            page = self.session.get_active_page()
            self.uploads.upload_files(page, target, file_paths)
            return BrowserActionResult(
                success=True,
                action="upload",
                url=page.url,
                title=page.title(),
                message="File uploaded successfully",
            )
        except Exception as e:
            return BrowserActionResult(
                success=False,
                action="upload",
                error=str(e),
            )

    def fill_form(self, fields: Dict[Union[str, dict], str]) -> BrowserActionResult:
        try:
            page = self.session.get_active_page()
            self.forms.fill_form(page, fields)
            return BrowserActionResult(
                success=True,
                action="fill_form",
                url=page.url,
                title=page.title(),
                message="Form fields populated",
            )
        except Exception as e:
            return BrowserActionResult(
                success=False,
                action="fill_form",
                error=str(e),
            )

    def submit_form(self, target: Optional[Union[str, dict]] = None) -> BrowserActionResult:
        try:
            page = self.session.get_active_page()
            self.forms.submit_form(page, target)
            self._check_captcha(page)
            return BrowserActionResult(
                success=True,
                action="submit_form",
                url=page.url,
                title=page.title(),
                message="Form submitted successfully",
            )
        except CaptchaDetectedError as ce:
            return BrowserActionResult(
                success=False,
                action="submit_form",
                message="HUMAN_INTERVENTION_REQUIRED",
                error=str(ce),
            )
        except Exception as e:
            return BrowserActionResult(
                success=False,
                action="submit_form",
                error=str(e),
            )

    # -------------------------------------------------------------------------
    # Visual Screenshot (Optional)
    # -------------------------------------------------------------------------

    def screenshot(self, path: Optional[str] = None, full_page: bool = False) -> str:
        """Takes a screenshot only when explicitly requested by user or diagnostic system."""
        page = self.session.get_active_page()
        if not path:
            out_dir = Path("data/screenshots")
            out_dir.mkdir(parents=True, exist_ok=True)
            path = str(out_dir / f"browser_{int(page.evaluate('Date.now()'))}.png")

        page.screenshot(path=path, full_page=full_page)
        logger.info("Browser screenshot saved to %s", path)
        return str(Path(path).resolve())

    # -------------------------------------------------------------------------
    # Internal Helpers
    # -------------------------------------------------------------------------

    def _check_captcha(self, page: Page) -> None:
        try:
            content = page.content().lower()
            for sig in CAPTCHA_SIGNATURES:
                if sig in content:
                    logger.warning("CAPTCHA or anti-bot challenge detected on page (%s): %s", page.url, sig)
                    raise CaptchaDetectedError(
                        f"Anti-bot security check or CAPTCHA detected on {page.url} ({sig}). HUMAN_INTERVENTION_REQUIRED"
                    )
        except CaptchaDetectedError:
            raise
        except Exception:
            pass
