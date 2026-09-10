"""
Unit tests for OCRProvider.
"""

import pytest
from PIL import Image
from jarvis.computer.vision.ocr import OCRProvider


def test_ocr_provider_extraction():
    ocr = OCRProvider()
    assert ocr.is_available() is True

    img = Image.new("RGB", (300, 300), color=(250, 250, 250))
    regions = ocr.extract_regions(img)

    assert len(regions) > 0
    for reg in regions:
        assert reg.text is not None
        assert reg.confidence >= 0.0
        assert reg.width > 0
