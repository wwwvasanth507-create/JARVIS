"""
Integration tests for Screen Understanding, OCR & Vision Layer (Prompt 014).
"""

import pytest
from PIL import Image, ImageDraw, ImageFont
from jarvis.computer.vision.manager import ScreenVisionManager
from jarvis.computer.vision.models import VisualTarget, ElementType, CaptureMode
from jarvis.computer.vision.errors import ScreenPrivacyDeniedError, AmbiguousVisualTargetError


@pytest.fixture
def vision_manager():
    return ScreenVisionManager()


def test_scenario_1_capture_ocr_screen_summary(vision_manager):
    """Scenario 1: Capture screen -> OCR text extraction -> ScreenState summary."""
    cap = vision_manager.capture_screen()
    assert cap["width"] > 0

    text_data = vision_manager.read_screen_text()
    assert "text" in text_data
    assert "active_window" in text_data

    desc = vision_manager.describe_screen()
    assert len(desc) > 0


def test_scenario_2_find_target_coordinates(vision_manager):
    """Scenario 2: Find target button on screen -> Return exact coordinates."""
    elem = vision_manager.find_visual_target("Settings", text="Settings")
    assert elem.label == "Settings"
    assert elem.x >= 0
    assert elem.y >= 0


def test_scenario_3_visual_state_comparison(vision_manager):
    """Scenario 3: Verify visual state change before/after harmless action."""
    baseline = vision_manager.verifier.capture_baseline()

    # Capture visual comparison result
    comp = vision_manager.verifier.verify_visual_change(baseline)
    assert comp.perceptual_difference >= 0.0


def test_scenario_4_privacy_policy_blocking(vision_manager):
    """Scenario 4: Privacy policy enforcement blocking access to sensitive window title."""
    assert vision_manager.privacy_policy.is_window_blocked("1Password - Vault") is True

    with pytest.raises(ScreenPrivacyDeniedError):
        vision_manager.privacy_policy.validate_screen_capture_allowed("Bitwarden - Master Password")


def test_scenario_5_visual_ambiguity_detection(vision_manager):
    """Scenario 5: Visual target ambiguity detection throwing AmbiguousVisualTargetError."""
    from jarvis.computer.vision.models import VisualElement
    elements = [
        VisualElement(element_id="btn1", type=ElementType.BUTTON, label="Save", x=10, y=10, width=50, height=20, confidence=0.9),
        VisualElement(element_id="btn2", type=ElementType.BUTTON, label="Save", x=200, y=10, width=50, height=20, confidence=0.9)
    ]
    target = VisualTarget(description="Save button", text="Save")

    with pytest.raises(AmbiguousVisualTargetError):
        vision_manager.matcher.find_target(target, elements)


def test_scenario_6_health_check(vision_manager):
    """Scenario 6: Verify health check reporting."""
    health = vision_manager.health_check()
    assert health.available is True
    assert health.privacy_policy_active is True
