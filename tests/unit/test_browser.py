"""
Unit tests for JARVIS Browser Automation and Controlled Internet Access layer.
"""

from pathlib import Path
import pytest
from unittest.mock import MagicMock, patch

from jarvis.core.config import BrowserSettings
from jarvis.browser.manager import BrowserManager
from jarvis.browser.navigation import validate_url
from jarvis.browser.selectors import SelectorEngine
from jarvis.browser.state import BrowserState, TabInfo, BrowserActionResult
from jarvis.browser.errors import SecurityViolationError, CaptchaDetectedError, TargetNotFoundError
from jarvis.tools.browser_tools import (
    BrowserOpenTool,
    BrowserGotoTool,
    BrowserReadPageTool,
    BrowserSearchTool,
    BrowserClickTool,
    BrowserFillTool,
    BrowserGetStateTool,
    BROWSER_TOOLS,
)


def test_url_validation():
    """Test URL protocol scheme and formatting validation."""
    assert validate_url("https://www.google.com") == "https://www.google.com"
    assert validate_url("http://localhost:8000") == "http://localhost:8000"
    assert validate_url("youtube.com") == "https://youtube.com"

    with pytest.raises(SecurityViolationError):
        validate_url("javascript:alert(1)")

    with pytest.raises(SecurityViolationError):
        validate_url("file:///C:/Windows/System32/cmd.exe", allowed_schemes=["http", "https"])


def test_selector_engine_resolution():
    """Test selector engine target resolution for strings and dicts."""
    engine = SelectorEngine()
    mock_page = MagicMock()
    mock_locator = MagicMock()
    mock_locator.count.return_value = 1
    mock_locator.first = mock_locator
    mock_page.locator.return_value = mock_locator
    mock_page.get_by_role.return_value = mock_locator

    # CSS string
    loc, desc = engine.resolve_locator(mock_page, "#search-box")
    assert "CSS selector" in desc

    # Accessible role and name
    loc, desc = engine.resolve_locator(mock_page, {"role": "button", "name": "Search"})
    assert "role 'button'" in desc


def test_browser_settings_defaults():
    """Test browser configuration model."""
    settings = BrowserSettings()
    assert settings.engine == "chromium"
    assert settings.reuse_session is True
    assert settings.persistent_profile is True
    assert settings.default_timeout_ms == 10000
    assert settings.navigation_timeout_ms == 15000


def test_browser_state_model():
    """Test BrowserState serialization and metadata handling."""
    tab1 = TabInfo(id="0", url="https://youtube.com", title="YouTube", is_active=True)
    tab2 = TabInfo(id="1", url="https://google.com", title="Google", is_active=False)
    state = BrowserState(
        running=True,
        current_url="https://youtube.com",
        current_title="YouTube",
        active_tab_id="0",
        tabs=[tab1, tab2],
    )
    assert state.running is True
    assert len(state.tabs) == 2
    assert state.tabs[0].is_active is True


def test_browser_tools_registration():
    """Verify tool metadata, schemas, and counts in BROWSER_TOOLS registry."""
    assert len(BROWSER_TOOLS) == 20
    tool_names = [t.name for t in BROWSER_TOOLS]

    expected = [
        "browser.open", "browser.goto", "browser.back", "browser.forward", "browser.reload",
        "browser.tabs.list", "browser.tabs.new", "browser.tabs.switch", "browser.tabs.close",
        "browser.read_page", "browser.search", "browser.click", "browser.fill", "browser.type",
        "browser.press", "browser.scroll", "browser.download", "browser.upload",
        "browser.get_state", "browser.screenshot"
    ]
    for exp in expected:
        assert exp in tool_names


@patch("jarvis.tools.browser_tools.get_browser_manager")
def test_browser_open_tool_execution(mock_get_mgr):
    """Test tool execution logic for browser.open with permission check."""
    mock_mgr = MagicMock()
    mock_mgr.open.return_value = BrowserActionResult(
        success=True, action="goto", url="https://www.youtube.com", title="YouTube", message="Loaded"
    )
    mock_get_mgr.return_value = mock_mgr

    tool = BrowserOpenTool()
    res = tool.execute(url="https://www.youtube.com")

    assert res.success is True
    assert res.data["url"] == "https://www.youtube.com"
    mock_mgr.open.assert_called_once_with("https://www.youtube.com")


@patch("jarvis.tools.browser_tools.get_browser_manager")
def test_browser_get_state_tool(mock_get_mgr):
    """Test tool execution for browser.get_state."""
    mock_mgr = MagicMock()
    mock_mgr.get_state.return_value = BrowserState(
        running=True,
        current_url="https://duckduckgo.com",
        current_title="DuckDuckGo",
        active_tab_id="0",
        tabs=[TabInfo(id="0", url="https://duckduckgo.com", title="DuckDuckGo", is_active=True)],
    )
    mock_get_mgr.return_value = mock_mgr

    tool = BrowserGetStateTool()
    res = tool.execute()

    assert res.success is True
    assert res.data["running"] is True
    assert res.data["current_url"] == "https://duckduckgo.com"
