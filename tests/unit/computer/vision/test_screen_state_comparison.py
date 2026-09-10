"""
Unit tests for ScreenStateManager and ScreenComparator.
"""

import pytest
from PIL import Image
from jarvis.computer.vision.state import ScreenStateManager
from jarvis.computer.vision.comparison import ScreenComparator


def test_screen_state_and_comparison():
    img1 = Image.new("RGB", (200, 200), color=(250, 250, 250))
    img2 = Image.new("RGB", (200, 200), color=(10, 10, 10))

    state1 = ScreenStateManager.build_state(img1, active_window="App V1")
    state2 = ScreenStateManager.build_state(img2, active_window="App V2")

    res = ScreenComparator.compare_states(state1, state2)
    assert res.changed is True
    assert res.perceptual_difference >= 0.0
