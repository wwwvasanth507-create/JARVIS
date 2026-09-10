"""
Data models for JARVIS Screen Understanding, OCR & Vision subsystem.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CaptureMode(str, Enum):
    FULL_SCREEN = "FULL_SCREEN"
    ACTIVE_WINDOW = "ACTIVE_WINDOW"
    REGION = "REGION"


class ElementType(str, Enum):
    BUTTON = "BUTTON"
    TEXT = "TEXT"
    INPUT = "INPUT"
    CHECKBOX = "CHECKBOX"
    ICON = "ICON"
    LINK = "LINK"
    MENU = "MENU"
    TAB = "TAB"
    WINDOW = "WINDOW"
    IMAGE = "IMAGE"
    UNKNOWN = "UNKNOWN"


class OCRTextRegion(BaseModel):
    text: str
    confidence: float
    x: int
    y: int
    width: int
    height: int


class VisualElement(BaseModel):
    element_id: str
    type: ElementType
    label: str
    x: int
    y: int
    width: int
    height: int
    confidence: float
    source: str = "OCR" # DOM, OCR, TEMPLATE, VLM, COORDINATES


class VisualTarget(BaseModel):
    description: str
    text: Optional[str] = None
    element_type: ElementType = ElementType.UNKNOWN
    expected_region: Optional[List[int]] = None # [x, y, w, h]
    confidence_threshold: float = 0.6


class ScreenState(BaseModel):
    timestamp: float
    screen_size: Dict[str, int] # {"width": 1920, "height": 1080}
    active_window: str = "Unknown"
    ocr_regions: List[OCRTextRegion] = Field(default_factory=list)
    detected_elements: List[VisualElement] = Field(default_factory=list)
    visual_summary: str = ""
    source: str = "ScreenVisionManager"
    screen_hash: str = ""


class VisionHealth(BaseModel):
    available: bool
    ocr_backend: str
    vision_model_backend: str
    capture_available: bool
    privacy_policy_active: bool
    last_error: Optional[str] = None


class VisualComparisonResult(BaseModel):
    changed: bool
    perceptual_difference: float
    ocr_difference_count: int
    description: str
