"""
Screen Understanding, OCR & Vision package for JARVIS.
"""

from jarvis.computer.vision.errors import (
    VisionError,
    ScreenCaptureUnavailableError,
    OCRUnavailableError,
    VisionModelUnavailableError,
    ScreenPrivacyDeniedError,
    VisualTargetNotFoundError,
    AmbiguousVisualTargetError,
    VisionAnalysisTimeoutError,
    VisionVerificationFailedError,
)
from jarvis.computer.vision.models import (
    CaptureMode,
    ElementType,
    OCRTextRegion,
    VisualElement,
    VisualTarget,
    ScreenState,
    VisionHealth,
    VisualComparisonResult,
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
from jarvis.computer.vision.manager import ScreenVisionManager

__all__ = [
    "VisionError",
    "ScreenCaptureUnavailableError",
    "OCRUnavailableError",
    "VisionModelUnavailableError",
    "ScreenPrivacyDeniedError",
    "VisualTargetNotFoundError",
    "AmbiguousVisualTargetError",
    "VisionAnalysisTimeoutError",
    "VisionVerificationFailedError",
    "CaptureMode",
    "ElementType",
    "OCRTextRegion",
    "VisualElement",
    "VisualTarget",
    "ScreenState",
    "VisionHealth",
    "VisualComparisonResult",
    "ScreenPrivacyPolicy",
    "ScreenCapture",
    "ImagePreprocessor",
    "VisionCache",
    "OCRProvider",
    "UIElementDetector",
    "LayoutAnalyzer",
    "VisualTargetMatcher",
    "ScreenStateManager",
    "ScreenComparator",
    "ScreenAnalyzer",
    "VisualVerificationManager",
    "ScreenVisionManager",
]
