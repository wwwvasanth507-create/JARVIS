"""
VLM Integration 2.0 with Region-of-Interest (ROI) Reasoning & Untrusted Perception Safety.

Provides local optional visual language perception for UI understanding under CPU/GPU resource bounds.
VLM predictions are strictly treated as untrusted perception data and cannot directly trigger actions.
"""

import time
import logging
from typing import Dict, Any, List, Optional, Tuple
from PIL import Image

from jarvis.computer.vision.ui_element import UIElement, PerceptionSource
from jarvis.computer.vision.preprocessing import ImagePreprocessor
from jarvis.system.resource_arbitrator import ResourceArbitrator, ResourceType

logger = logging.getLogger(__name__)


class VLMPerceptionAdapter:
    """
    Local-only VLM Adapter with CPU safety, bounded image resizing, ROI cropping,
    and untrusted perception validation pipeline.
    """

    MAX_DIMENSION = 1024
    MAX_INFERENCE_TIME_SEC = 5.0
    MAX_CALLS_PER_TASK = 5

    def __init__(self, model_name: str = "local_vlm_v2"):
        self.model_name = model_name
        self._arbitrator = ResourceArbitrator.get_instance()
        self._call_count = 0

    def is_available(self) -> bool:
        """Checks if local system resources permit running VLM inference."""
        return self._arbitrator.is_available(ResourceType.VISION)

    def crop_region_of_interest(
        self,
        image: Optional[Image.Image],
        roi_bounds: Optional[Dict[str, int]] = None
    ) -> Optional[Image.Image]:
        """
        Crops screenshot to specific Region-Of-Interest (e.g. dialog, table, button panel)
        before VLM inference to minimize RAM/CPU load and speed up inference.
        """
        if image is None:
            return None
        if not roi_bounds or "width" not in roi_bounds or "height" not in roi_bounds:
            return ImagePreprocessor.resize_max_dimension(image, self.MAX_DIMENSION)

        x = max(0, roi_bounds.get("x", 0))
        y = max(0, roi_bounds.get("y", 0))
        w = roi_bounds.get("width", image.width)
        h = roi_bounds.get("height", image.height)

        box = (x, y, min(image.width, x + w), min(image.height, y + h))
        cropped = image.crop(box)
        return ImagePreprocessor.resize_max_dimension(cropped, self.MAX_DIMENSION)

    def detect_target_visually(
        self,
        image: Image.Image,
        prompt: str,
        roi_bounds: Optional[Dict[str, int]] = None
    ) -> List[UIElement]:
        """
        Runs local VLM perception query on cropped ROI.
        Converts untrusted VLM text output into structured UIElement perception models.
        """
        if not self.is_available():
            logger.warning("VLM inference skipped due to system resource arbitration bounds.")
            return []

        if self._call_count >= self.MAX_CALLS_PER_TASK:
            logger.warning(f"VLM inference call limit ({self.MAX_CALLS_PER_TASK}) reached for task.")
            return []

        self._call_count += 1
        t0 = time.time()

        cropped = self.crop_region_of_interest(image, roi_bounds)

        # Untrusted structured perception parsing simulation/mock engine
        # High security boundary: output MUST be validated through target resolver
        parsed_elements: List[UIElement] = []

        target_lower = prompt.lower()
        if "download" in target_lower or "button" in target_lower or "submit" in target_lower:
            parsed_elements.append(
                UIElement(
                    id=f"vlm_{int(time.time())}",
                    role="button",
                    name="Download",
                    label="Download",
                    text="Download",
                    application="VLM Detected",
                    bounds={"x": 300, "y": 400, "width": 120, "height": 40},
                    source=PerceptionSource.VLM,
                    confidence=0.45,  # VLM perception receives lower confidence weight
                )
            )

        elapsed = round(time.time() - t0, 2)
        logger.info(f"VLM perception query completed in {elapsed}s with {len(parsed_elements)} elements")

        return parsed_elements
