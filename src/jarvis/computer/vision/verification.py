"""
Visual verification manager integrating visual evidence into action verification.
"""

from typing import Dict, Any, Optional
from PIL import Image
from jarvis.computer.vision.capture import ScreenCapture
from jarvis.computer.vision.comparison import ScreenComparator
from jarvis.computer.vision.models import VisualComparisonResult, ScreenState
from jarvis.computer.vision.errors import VisionVerificationFailedError


class VisualVerificationManager:
    """
    Verifies computer control actions using visual evidence (before/after screenshot comparison).
    Prevents false success claims when actions fail to alter visual/system state.
    """

    def __init__(self, capture: Optional[ScreenCapture] = None):
        self.capture = capture or ScreenCapture()

    def capture_baseline(self) -> Dict[str, Any]:
        return self.capture.capture_full_screen()


    def verify_visual_change(
        self,
        before_capture: Dict[str, Any],
        expected_change_description: Optional[str] = None
    ) -> VisualComparisonResult:
        """
        Captures current screen and compares with before_capture baseline.
        """
        after_capture = self.capture.capture_full_screen()

        before_img: Image.Image = before_capture["image"]
        after_img: Image.Image = after_capture["image"]

        res = ScreenComparator.compare_images(before_img, after_img)

        # Also check window change
        if before_capture.get("active_window") != after_capture.get("active_window"):
            res.changed = True
            res.description += f" (Active window changed from '{before_capture.get('active_window')}' to '{after_capture.get('active_window')}')"

        return res
