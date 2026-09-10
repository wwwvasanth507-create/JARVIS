"""
Central ScreenVisionManager facade.
"""

from typing import Dict, Any, List, Optional, Tuple
from PIL import Image
from jarvis.computer.vision.models import (
    ScreenState, VisualElement, OCRTextRegion, VisualTarget,
    VisionHealth, CaptureMode, VisualComparisonResult
)
from jarvis.computer.vision.privacy import ScreenPrivacyPolicy
from jarvis.computer.vision.capture import ScreenCapture
from jarvis.computer.vision.preprocessing import ImagePreprocessor
from jarvis.computer.vision.cache import VisionCache
from jarvis.computer.vision.ocr import OCRProvider
from jarvis.computer.vision.detector import UIElementDetector
from jarvis.computer.vision.layout import LayoutAnalyzer
from jarvis.computer.vision.matching import VisualTargetMatcher
from jarvis.computer.vision.state import ScreenStateManager
from jarvis.computer.vision.comparison import ScreenComparator
from jarvis.computer.vision.analyzer import ScreenAnalyzer
from jarvis.computer.vision.verification import VisualVerificationManager


class ScreenVisionManager:
    """
    Central manager for local screen understanding, OCR, element detection, and visual verification.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        privacy_enabled = self.config.get("privacy_enabled", True)
        cache_ttl = self.config.get("cache_ttl_seconds", 30.0)

        self.privacy_policy = ScreenPrivacyPolicy(enabled=privacy_enabled)
        self.capture = ScreenCapture(self.privacy_policy)
        self.preprocessor = ImagePreprocessor()
        self.cache = VisionCache(ttl_seconds=cache_ttl)
        self.ocr_provider = OCRProvider()
        self.detector = UIElementDetector(self.ocr_provider)
        self.layout_analyzer = LayoutAnalyzer()
        self.matcher = VisualTargetMatcher()
        self.analyzer = ScreenAnalyzer(self.capture, self.ocr_provider, self.detector)
        self.verifier = VisualVerificationManager(self.capture)
        self.comparator = ScreenComparator()

    def capture_screen(
        self,
        mode: CaptureMode = CaptureMode.FULL_SCREEN,
        region: Optional[Tuple[int, int, int, int]] = None
    ) -> Dict[str, Any]:
        return self.capture.capture(mode=mode, region=region)

    def read_screen_text(self, mode: CaptureMode = CaptureMode.FULL_SCREEN) -> Dict[str, Any]:
        cap = self.capture_screen(mode=mode)
        img: Image.Image = cap["image"]
        screen_hash = self.preprocessor.compute_perceptual_hash(img)

        cached_text = self.cache.get(screen_hash, "ocr_text")
        cached_regions = self.cache.get(screen_hash, "ocr_regions")

        if cached_text is None or cached_regions is None:
            regions = self.ocr_provider.extract_regions(img)
            text = " ".join([r.text for r in regions if r.text.strip()])
            self.cache.set(screen_hash, "ocr_text", text)
            self.cache.set(screen_hash, "ocr_regions", regions)
            cached_text = text
            cached_regions = regions

        return {
            "text": cached_text,
            "regions": [r.model_dump() for r in cached_regions],
            "active_window": cap["active_window"],
            "screen_hash": screen_hash
        }

    def analyze_screen(self) -> ScreenState:
        return self.analyzer.analyze_screen()


    def describe_screen(self) -> str:
        return self.analyzer.describe_screen()

    def find_visual_target(self, description: str, text: Optional[str] = None) -> VisualElement:
        state = self.analyze_screen()
        target = VisualTarget(description=description, text=text)
        return self.matcher.find_target(target, state.detected_elements)

    def compare_screen_states(self, before_state: ScreenState, after_state: ScreenState) -> VisualComparisonResult:
        return self.comparator.compare_states(before_state, after_state)

    def health_check(self) -> VisionHealth:
        return VisionHealth(
            available=True,
            ocr_backend=self.ocr_provider.get_backend_name(),
            vision_model_backend="cpu_deterministic",
            capture_available=True,
            privacy_policy_active=self.privacy_policy.enabled,
            last_error=None
        )
