"""
Unit tests for WindowsKeyboard text typing, key presses, and hotkey execution.
"""

import pytest
from jarvis.computer.windows.keyboard import WindowsKeyboard


def test_keyboard_vk_resolution():
    assert WindowsKeyboard._resolve_vk_code("ENTER") is not None
    assert WindowsKeyboard._resolve_vk_code("ESC") is not None
    assert WindowsKeyboard._resolve_vk_code("A") == ord("A")
    assert WindowsKeyboard._resolve_vk_code("F5") is not None
    assert WindowsKeyboard._resolve_vk_code("INVALID_KEY_123") is None


def test_keyboard_press_key_safety():
    # Valid key
    res = WindowsKeyboard.press_key("SHIFT")
    assert res.success is True
    assert res.status == "SUCCESS"

    # Invalid key rejected safely
    res_bad = WindowsKeyboard.press_key("NON_EXISTENT_KEY")
    assert res_bad.success is False
    assert res_bad.status == "DENIED"


def test_keyboard_hotkey_safety():
    # Valid hotkey
    res = WindowsKeyboard.hotkey(["CTRL", "A"])
    assert res.success is True
    assert res.status == "SUCCESS"

    # Invalid hotkey rejected safely
    res_bad = WindowsKeyboard.hotkey(["CTRL", "BAD_KEY"])
    assert res_bad.success is False
    assert res_bad.status == "DENIED"
