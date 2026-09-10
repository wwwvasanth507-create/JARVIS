"""
Unit tests for WindowsWindowManager window enumeration and state queries.
"""

import pytest
from jarvis.computer.windows.window import WindowsWindowManager
from jarvis.computer.windows.screen import WindowsScreen


def test_window_enumeration():
    windows = WindowsWindowManager.list_windows()
    assert isinstance(windows, list)
    assert len(windows) > 0

    active_win = WindowsWindowManager.get_active_window()
    assert active_win is not None
    assert active_win.title != ""


def test_screen_size_and_screenshot():
    sz = WindowsScreen.get_screen_size()
    assert sz.width > 0
    assert sz.height > 0

    shot_res = WindowsScreen.screenshot(active_window_only=False)
    assert shot_res.success is True
    assert shot_res.verified is True
    assert shot_res.data["width"] == sz.width
    assert shot_res.data["height"] == sz.height
