"""
Unit tests for ScreenCapture.
"""

import pytest
from jarvis.computer.vision.capture import ScreenCapture
from jarvis.computer.vision.models import CaptureMode


def test_screen_capture_full_screen():
    capture = ScreenCapture()
    res = capture.capture_full_screen()
    assert res["width"] > 0
    assert res["height"] > 0
    assert res["mode"] == "FULL_SCREEN"
    assert "image" in res


def test_screen_capture_region():
    capture = ScreenCapture()
    res = capture.capture_region((0, 0, 100, 100))
    assert res["width"] == 100
    assert res["height"] == 100
    assert res["mode"] == "REGION"
