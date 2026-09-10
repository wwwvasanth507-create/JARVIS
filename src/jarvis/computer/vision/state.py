"""
ScreenState manager and compact context builder.
"""

import time
from typing import List, Dict, Any, Optional
from PIL import Image
from jarvis.computer.vision.models import ScreenState, OCRTextRegion, VisualElement
from jarvis.computer.vision.preprocessing import ImagePreprocessor


class ScreenStateManager:
    """
    Constructs compact ScreenState objects containing structured UI elements and text summaries.
    Does NOT store raw image bytes inside the orchestration context window.
    """

    @staticmethod
    def build_state(
        image: Image.Image,
        active_window: str = "Desktop",
        ocr_regions: Optional[List[OCRTextRegion]] = None,
        detected_elements: Optional[List[VisualElement]] = None
    ) -> ScreenState:
        ocr_regs = ocr_regions or []
        elems = detected_elements or []
        screen_hash = ImagePreprocessor.compute_perceptual_hash(image)

        summary_parts = [f"Active Window: {active_window}"]
        if elems:
            summary_parts.append(f"UI Elements: {len(elems)} ({', '.join([e.label for e in elems[:5]])})")
        elif ocr_regs:
            summary_parts.append(f"Text Snippet: {' '.join([r.text for r in ocr_regs[:5]])}")

        return ScreenState(
            timestamp=time.time(),
            screen_size={"width": image.width, "height": image.height},
            active_window=active_window,
            ocr_regions=ocr_regs,
            detected_elements=elems,
            visual_summary=" | ".join(summary_parts),
            source="ScreenStateManager",
            screen_hash=screen_hash
        )
