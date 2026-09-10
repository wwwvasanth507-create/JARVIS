"""
High-level screen analysis and description engine.
"""

from typing import Dict, Any, Optional, List
from PIL import Image
from jarvis.computer.vision.capture import ScreenCapture
from jarvis.computer.vision.ocr import OCRProvider
from jarvis.computer.vision.detector import UIElementDetector
from jarvis.computer.vision.state import ScreenStateManager
from jarvis.computer.vision.models import ScreenState, VisualElement


class ScreenAnalyzer:
    """
    High-level analyzer for screen descriptions and visual element extraction.
    """

    def __init__(
        self,
        capture: Optional[ScreenCapture] = None,
        ocr: Optional[OCRProvider] = None,
        detector: Optional[UIElementDetector] = None
    ):
        self.capture = capture or ScreenCapture()
        self.ocr = ocr or OCRProvider()
        self.detector = detector or UIElementDetector(self.ocr)

    def analyze_screen(self) -> ScreenState:
        """
        Captures screen, extracts OCR text, detects UI elements, and constructs ScreenState.
        """
        cap = self.capture.capture_full_screen()
        img: Image.Image = cap["image"]
        active_window = cap["active_window"]

        ocr_regions = self.ocr.extract_regions(img)
        elements = self.detector.detect_elements(img, ocr_regions)

        return ScreenStateManager.build_state(
            image=img,
            active_window=active_window,
            ocr_regions=ocr_regions,
            detected_elements=elements
        )

    def describe_screen(self) -> str:
        """
        Returns a concise natural language description of current screen content.
        """
        state = self.analyze_screen()
        parts = [f"Screen shows active window '{state.active_window}' ({state.screen_size['width']}x{state.screen_size['height']})."]

        if state.detected_elements:
            labels = [e.label for e in state.detected_elements[:6]]
            parts.append(f"Visible UI elements include: {', '.join(labels)}.")
        elif state.ocr_regions:
            txts = [r.text for r in state.ocr_regions[:6]]
            parts.append(f"Visible text snippets include: {', '.join(txts)}.")

        return " ".join(parts)
