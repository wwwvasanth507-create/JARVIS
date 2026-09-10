"""
Unit tests for UIElementDetector.
"""

import pytest
from PIL import Image
from jarvis.computer.vision.detector import UIElementDetector
from jarvis.computer.vision.models import ElementType, OCRTextRegion


def test_ui_element_detector():
    detector = UIElementDetector()
    img = Image.new("RGB", (300, 300), color=(250, 250, 250))
    ocr_regions = [
        OCRTextRegion(text="Settings", confidence=0.95, x=10, y=10, width=50, height=20),
        OCRTextRegion(text="File", confidence=0.90, x=70, y=10, width=40, height=20)
    ]

    elements = detector.detect_elements(img, ocr_regions)
    assert len(elements) == 2
    assert elements[0].type == ElementType.BUTTON
    assert elements[1].type == ElementType.MENU
