"""
UI State Model, State Diff Engine, and Target Resolver for JARVIS.

Provides structured desktop UI state representations, before/after state diffing,
perception confidence scoring (HIGH, MEDIUM, LOW), and multi-layer target resolution.
"""

from enum import Enum
import time
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class PerceptionConfidence(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class UIElementDescriptor(BaseModel):
    element_id: str
    role: str  # "button", "input", "checkbox", "tab", "dialog"
    label: str
    location: Dict[str, int] = Field(default_factory=dict)  # {x, y, width, height}
    is_enabled: bool = True
    confidence: PerceptionConfidence = PerceptionConfidence.HIGH


class UIStateModel(BaseModel):
    active_application: str = "Unknown"
    window_title: str = ""
    elements: List[UIElementDescriptor] = Field(default_factory=list)
    dialog_present: bool = False
    loading: bool = False
    timestamp: float = Field(default_factory=time.time)


class UIStateDiffEngine:
    """Computes structured differences between two UI states."""

    @classmethod
    def compute_diff(cls, state_before: UIStateModel, state_after: UIStateModel) -> Dict[str, Any]:
        app_changed = state_before.active_application != state_after.active_application
        title_changed = state_before.window_title != state_after.window_title
        dialog_appeared = not state_before.dialog_present and state_after.dialog_present
        loading_finished = state_before.loading and not state_after.loading

        return {
            "application_changed": app_changed,
            "title_changed": title_changed,
            "dialog_appeared": dialog_appeared,
            "loading_finished": loading_finished,
            "meaningful_change_detected": app_changed or title_changed or dialog_appeared or loading_finished
        }


class SemanticTargetResolver:
    """Resolves UI target elements using a multi-layer strategy."""

    @classmethod
    def resolve_target(cls, state: UIStateModel, target_label: str) -> Optional[UIElementDescriptor]:
        target_lower = target_label.lower()
        # Search structured elements
        for elem in state.elements:
            if target_lower in elem.label.lower():
                return elem
        return None
