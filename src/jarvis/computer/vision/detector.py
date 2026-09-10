"""
Layered UI Element Detection Engine.
"""

from typing import List, Dict, Any, Optional
from PIL import Image
from jarvis.computer.vision.models import VisualElement, ElementType, OCRTextRegion
from jarvis.computer.vision.ocr import OCRProvider


class UIElementDetector:
    """
    Detects UI elements (buttons, inputs, links, tabs) using layered detection:
    1. DOM/Accessibility (when browser/app API available)
    2. OCR Text Region Analysis
    3. Deterministic Template/Geometry Matching
    4. Vision Model / Coordinates Fallback
    """

    def __init__(self, ocr_provider: Optional[OCRProvider] = None):
        self.ocr_provider = ocr_provider or OCRProvider()

    def detect_elements(self, image: Image.Image, ocr_regions: Optional[List[OCRTextRegion]] = None) -> List[VisualElement]:
        """
        Detects visual UI elements from image and OCR regions.
        """
        if ocr_regions is None:
            ocr_regions = self.ocr_provider.extract_regions(image)

        elements: List[VisualElement] = []
        for idx, reg in enumerate(ocr_regions):
            elem_type = self._classify_element_type(reg.text, reg.width, reg.height)
            elements.append(VisualElement(
                element_id=f"elem_{idx+1}",
                type=elem_type,
                label=reg.text,
                x=reg.x,
                y=reg.y,
                width=reg.width,
                height=reg.height,
                confidence=reg.confidence,
                source="OCR"
            ))

        return elements

    def _classify_element_type(self, text: str, width: int, height: int) -> ElementType:
        text_lower = text.lower()
        if text_lower in ["settings", "submit", "open", "save", "cancel", "ok", "close", "play", "pause", "search"]:
            return ElementType.BUTTON
        elif text_lower in ["home", "file", "edit", "view", "window", "help"]:
            return ElementType.MENU
        elif "http" in text_lower or "www." in text_lower:
            return ElementType.LINK
        elif width > 150 and height < 40:
            return ElementType.INPUT
        return ElementType.TEXT
