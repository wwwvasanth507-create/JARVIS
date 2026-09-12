"""
Playwright Browser Session Manager for JARVIS.
Handles lazy browser launching, persistent session context reuse, and lifecycle management.
"""

from pathlib import Path
import time
import logging
from typing import Any, Dict, Optional
from playwright.sync_api import sync_playwright, Playwright, Browser, BrowserContext, Page

from jarvis.core.config import BrowserSettings
from jarvis.browser.errors import BrowserError

logger = logging.getLogger("jarvis.browser.session")


class BrowserSession:
    """Manages persistent Playwright browser process and context reuse."""

    _global_playwright: Optional[Playwright] = None

    @classmethod
    def stop_global_playwright(cls) -> None:
        if cls._global_playwright is not None:
            try:
                cls._global_playwright.stop()
            except Exception as e:
                logger.warning(f"Error stopping global Playwright instance: {e}")
            finally:
                cls._global_playwright = None

    def __init__(self, settings: Optional[BrowserSettings] = None):
        self.settings = settings or BrowserSettings()
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._active_page: Optional[Page] = None
        self._is_running = False

    @property
    def is_running(self) -> bool:
        return self._is_running and self._context is not None

    def start(self) -> bool:
        """Launches Playwright browser engine lazily and initializes persistent session context."""
        if self.is_running:
            return True

        start_time = time.perf_counter()
        try:
            logger.info("Initializing Playwright engine...")
            if BrowserSession._global_playwright is None:
                BrowserSession._global_playwright = sync_playwright().start()
            self._playwright = BrowserSession._global_playwright

            engine_type = getattr(self._playwright, self.settings.engine, self._playwright.chromium)
            user_data_path = Path(self.settings.user_data_dir).resolve()
            user_data_path.mkdir(parents=True, exist_ok=True)
            download_path = Path(self.settings.download_dir).resolve()
            download_path.mkdir(parents=True, exist_ok=True)

            logger.info(f"Launching {self.settings.engine} (Headless: {self.settings.headless})")
            
            if self.settings.persistent_profile:
                self._context = engine_type.launch_persistent_context(
                    user_data_dir=str(user_data_path),
                    headless=self.settings.headless,
                    downloads_path=str(download_path),
                    accept_downloads=True,
                    viewport={"width": 1280, "height": 800},
                )
                pages = self._context.pages
                self._active_page = pages[0] if pages else self._context.new_page()
            else:
                self._browser = engine_type.launch(headless=self.settings.headless)
                self._context = self._browser.new_context(
                    downloads_path=str(download_path),
                    accept_downloads=True,
                    viewport={"width": 1280, "height": 800},
                )
                self._active_page = self._context.new_page()

            # Configure default timeouts
            self._context.set_default_timeout(self.settings.default_timeout_ms)
            self._context.set_default_navigation_timeout(self.settings.navigation_timeout_ms)

            self._is_running = True
            dur = time.perf_counter() - start_time
            logger.info(f"BROWSER_STARTED: Browser initialized in {dur*1000:.2f} ms")
            return True
        except Exception as e:
            logger.error(f"BROWSER_ERROR: Failed to start Playwright session: {e}")
            self.stop()
            return False

    def get_active_page(self) -> Page:
        """Returns current active Playwright Page instance, launching session if needed."""
        if not self.is_running:
            if not self.start():
                raise BrowserError("Could not initialize browser session.")

        if not self._active_page or self._active_page.is_closed():
            pages = self._context.pages if self._context else []
            self._active_page = pages[0] if pages else self._context.new_page()

        return self._active_page

    def get_context(self) -> BrowserContext:
        """Returns active Playwright BrowserContext."""
        if not self.is_running:
            self.start()
        return self._context

    def stop(self) -> None:
        """Stops browser context and releases session resources."""
        if not self._is_running and not self._browser and not self._context:
            return

        logger.info("BROWSER_STOPPED: Shutting down browser session...")
        try:
            if self._context:
                self._context.close()
            if self._browser:
                self._browser.close()
        except Exception as e:
            logger.warning(f"Error during browser session shutdown: {e}")
        finally:
            self._context = None
            self._browser = None
            self._playwright = None
            self._active_page = None
            self._is_running = False

    def restart(self) -> bool:
        """Restarts the browser session."""
        self.stop()
        return self.start()

