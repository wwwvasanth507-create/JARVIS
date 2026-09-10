"""
Safe Browser Automation Integration Test for JARVIS.
Navigates to local HTML fixture without internet dependency.
"""

from pathlib import Path
import pytest
from jarvis.browser.manager import BrowserManager
from jarvis.core.config import BrowserSettings


def test_local_browser_integration():
    """Tests browser lifecycle, navigation, reading, tabs, and cleanup on local HTML fixture."""
    fixture_path = Path("tests/browser/fixtures/sample_page.html").resolve()
    assert fixture_path.exists(), "Test fixture sample_page.html missing"

    file_url = fixture_path.as_uri()

    settings = BrowserSettings(
        headless=True,
        reuse_session=True,
        allowed_schemes=["http", "https", "file"],
    )
    manager = BrowserManager(settings=settings)

    try:
        # Start browser manager
        manager.start()
        assert manager.is_running() is True

        # Open local HTML fixture
        res = manager.open(file_url)
        assert res.success is True
        assert "JARVIS Test Page" in res.title

        # Read page structured content
        read_res = manager.read_page()
        assert read_res["title"] == "JARVIS Test Page"
        assert "JARVIS Browser Automation Test Page" in read_res["text"]
        assert len(read_res["links"]) >= 2
        assert len(read_res["forms"]) >= 1

        # Tab operations
        tab_res = manager.new_tab()
        assert tab_res.success is True
        tabs = manager.list_tabs()
        assert len(tabs) >= 2

        switch_res = manager.switch_tab(0)
        assert switch_res.success is True

        close_res = manager.close_tab(1)
        assert close_res.success is True

    finally:
        manager.stop()
        assert manager.is_running() is False
