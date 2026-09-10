"""
Unit tests for LayoutAnalyzer and VisualTargetMatcher.
"""

import pytest
from jarvis.computer.vision.matching import VisualTargetMatcher
from jarvis.computer.vision.models import VisualElement, VisualTarget, ElementType
from jarvis.computer.vision.errors import VisualTargetNotFoundError, AmbiguousVisualTargetError


def test_visual_target_matcher_success():
    matcher = VisualTargetMatcher()
    elements = [
        VisualElement(element_id="e1", type=ElementType.BUTTON, label="Settings", x=10, y=10, width=50, height=20, confidence=0.9),
        VisualElement(element_id="e2", type=ElementType.BUTTON, label="Cancel", x=100, y=10, width=50, height=20, confidence=0.9)
    ]

    target = VisualTarget(description="Settings button", text="Settings")
    match = matcher.find_target(target, elements)
    assert match.element_id == "e1"
    assert match.label == "Settings"


def test_visual_target_matcher_not_found():
    matcher = VisualTargetMatcher()
    elements = [VisualElement(element_id="e1", type=ElementType.BUTTON, label="Cancel", x=10, y=10, width=50, height=20, confidence=0.9)]
    target = VisualTarget(description="Settings button", text="Settings")

    with pytest.raises(VisualTargetNotFoundError):
        matcher.find_target(target, elements)


def test_visual_target_matcher_ambiguous():
    matcher = VisualTargetMatcher()
    elements = [
        VisualElement(element_id="e1", type=ElementType.BUTTON, label="Open", x=10, y=10, width=50, height=20, confidence=0.9),
        VisualElement(element_id="e2", type=ElementType.BUTTON, label="Open", x=100, y=10, width=50, height=20, confidence=0.9)
    ]
    target = VisualTarget(description="Open button", text="Open")

    with pytest.raises(AmbiguousVisualTargetError):
        matcher.find_target(target, elements)
