"""
Unified UI Element Model for JARVIS Perception System.
"""

from enum import Enum
import time
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class PerceptionSource(str, Enum):
    ACCESSIBILITY = "ACCESSIBILITY"
    DOM = "DOM"
    APPLICATION_API = "APPLICATION_API"
    OCR = "OCR"
    VISUAL = "VISUAL"
    VLM = "VLM"


SOURCE_CONFIDENCE_WEIGHTS: Dict[PerceptionSource, float] = {
    PerceptionSource.ACCESSIBILITY: 0.98,
    PerceptionSource.DOM: 0.95,
    PerceptionSource.APPLICATION_API: 0.90,
    PerceptionSource.OCR: 0.75,
    PerceptionSource.VISUAL: 0.60,
    PerceptionSource.VLM: 0.45,
}


class UIElement(BaseModel):
    """
    Common representation for all UI elements across Accessibility, DOM, OCR, and Vision sources.
    """
    id: str
    role: str = "element"  # e.g. "button", "input", "checkbox", "radio", "select", "table", "row", "cell", "form", "dialog", "link", "text", "region"
    name: str = ""
    label: str = ""
    text: str = ""
    value: str = ""
    placeholder: str = ""
    application: str = "Unknown"
    window: str = ""
    container: str = ""
    bounds: Dict[str, int] = Field(default_factory=dict)  # {x, y, width, height}
    enabled: bool = True
    visible: bool = True
    selected: bool = False
    focused: bool = False
    clickable: bool = True
    editable: bool = False
    source: PerceptionSource = PerceptionSource.ACCESSIBILITY
    confidence: float = 0.95
    timestamp: float = Field(default_factory=time.time)
    semantic_path: str = ""

    def get_effective_confidence(self) -> float:
        """Calculates final confidence combining source weight and perception confidence."""
        base_weight = SOURCE_CONFIDENCE_WEIGHTS.get(self.source, 0.5)
        return round(self.confidence * base_weight, 3)

    def center_point(self) -> Optional[Dict[str, int]]:
        """Returns center coordinates (x, y) if bounds are valid."""
        if not self.bounds or "x" not in self.bounds or "y" not in self.bounds:
            return None
        x = self.bounds["x"] + self.bounds.get("width", 0) // 2
        y = self.bounds["y"] + self.bounds.get("height", 0) // 2
        return {"x": x, "y": y}
