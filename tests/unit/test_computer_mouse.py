"""
Unit tests for WindowsMouse control operations.
"""

import pytest
from jarvis.computer.windows.mouse import WindowsMouse


def test_mouse_position_and_movement():
    pos = WindowsMouse.get_position()
    assert pos.x >= 0
    assert pos.y >= 0

    res = WindowsMouse.move(100, 100)
    assert res.success is True
    assert res.verified is True
    assert res.data["x"] == 100
    assert res.data["y"] == 100


def test_mouse_click_and_scroll():
    res_click = WindowsMouse.click(100, 100, button="left")
    assert res_click.success is True
    assert res_click.verified is True

    res_scroll = WindowsMouse.scroll(clicks=1, direction="down")
    assert res_scroll.success is True
    assert res_scroll.verified is True
