"""
UI State Model, Extended State Diff Engine, and Target Resolver for JARVIS.

Provides structured desktop/web UI state representations, before/after state diffing with classification,
perception confidence scoring, and multi-layer target resolution.
"""

from enum import Enum
import time
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from jarvis.computer.vision.ui_element import UIElement, PerceptionSource
from jarvis.computer.vision.snapshot import ScreenSemanticSnapshot

logger = logging.getLogger(__name__)


class PerceptionConfidence(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class UIElementDescriptor(BaseModel):
    element_id: str
    role: str = "button"  # "button", "input", "checkbox", "tab", "dialog"
    label: str = ""
    location: Dict[str, int] = Field(default_factory=dict)  # {x, y, width, height}
    is_enabled: bool = True
    confidence: PerceptionConfidence = PerceptionConfidence.HIGH

    def to_ui_element(self) -> UIElement:
        return UIElement(
            id=self.element_id,
            role=self.role,
            label=self.label,
            name=self.label,
            bounds=self.location,
            enabled=self.is_enabled,
            source=PerceptionSource.ACCESSIBILITY if self.confidence == PerceptionConfidence.HIGH else PerceptionSource.OCR,
            confidence=0.95 if self.confidence == PerceptionConfidence.HIGH else 0.75,
        )


class ChangeCategory(str, Enum):
    NO_CHANGE = "NO_CHANGE"
    MINOR_CHANGE = "MINOR_CHANGE"
    MAJOR_CHANGE = "MAJOR_CHANGE"
    NAVIGATION = "NAVIGATION"
    DIALOG_OPENED = "DIALOG_OPENED"
    DIALOG_CLOSED = "DIALOG_CLOSED"
    FORM_UPDATED = "FORM_UPDATED"
    TABLE_UPDATED = "TABLE_UPDATED"
    LOADING_STARTED = "LOADING_STARTED"
    LOADING_FINISHED = "LOADING_FINISHED"
    ERROR_APPEARED = "ERROR_APPEARED"
    SUCCESS_APPEARED = "SUCCESS_APPEARED"


class UIStateModel(BaseModel):
    active_application: str = "Unknown"
    window_title: str = ""
    url: Optional[str] = None
    elements: List[UIElementDescriptor] = Field(default_factory=list)
    semantic_elements: List[UIElement] = Field(default_factory=list)
    dialog_present: bool = False
    loading: bool = False
    error_present: bool = False
    success_present: bool = False
    timestamp: float = Field(default_factory=time.time)

    def to_snapshot(self) -> ScreenSemanticSnapshot:
        all_elems = list(self.semantic_elements)
        for desc in self.elements:
            all_elems.append(desc.to_ui_element())
        return ScreenSemanticSnapshot(
            application=self.active_application,
            window=self.window_title,
            url=self.url,
            elements=all_elems,
            loading_state=self.loading,
            timestamp=self.timestamp,
        )


class UIStateDiffEngine:
    """Computes structured differences between two UI states and classifies the change."""

    @classmethod
    def compute_diff(cls, state_before: UIStateModel, state_after: UIStateModel) -> Dict[str, Any]:
        app_changed = state_before.active_application != state_after.active_application
        title_changed = state_before.window_title != state_after.window_title
        url_changed = (state_before.url != state_after.url) if (state_before.url and state_after.url) else False
        dialog_appeared = not state_before.dialog_present and state_after.dialog_present
        dialog_closed = state_before.dialog_present and not state_after.dialog_present
        loading_started = not state_before.loading and state_after.loading
        loading_finished = state_before.loading and not state_after.loading
        error_appeared = not state_before.error_present and state_after.error_present
        success_appeared = not state_before.success_present and state_after.success_present

        categories: List[ChangeCategory] = []
        if app_changed or url_changed:
            categories.append(ChangeCategory.NAVIGATION)
        if dialog_appeared:
            categories.append(ChangeCategory.DIALOG_OPENED)
        if dialog_closed:
            categories.append(ChangeCategory.DIALOG_CLOSED)
        if loading_started:
            categories.append(ChangeCategory.LOADING_STARTED)
        if loading_finished:
            categories.append(ChangeCategory.LOADING_FINISHED)
        if error_appeared:
            categories.append(ChangeCategory.ERROR_APPEARED)
        if success_appeared:
            categories.append(ChangeCategory.SUCCESS_APPEARED)

        if not categories:
            if title_changed or len(state_before.elements) != len(state_after.elements):
                categories.append(ChangeCategory.MINOR_CHANGE)
            else:
                categories.append(ChangeCategory.NO_CHANGE)

        meaningful = any(
            c in categories
            for c in (
                ChangeCategory.NAVIGATION,
                ChangeCategory.DIALOG_OPENED,
                ChangeCategory.DIALOG_CLOSED,
                ChangeCategory.LOADING_FINISHED,
                ChangeCategory.ERROR_APPEARED,
                ChangeCategory.SUCCESS_APPEARED,
                ChangeCategory.MAJOR_CHANGE,
            )
        )

        return {
            "application_changed": app_changed,
            "title_changed": title_changed,
            "url_changed": url_changed,
            "dialog_appeared": dialog_appeared,
            "dialog_closed": dialog_closed,
            "loading_finished": loading_finished,
            "error_appeared": error_appeared,
            "success_appeared": success_appeared,
            "categories": [c.value for c in categories],
            "primary_category": categories[0].value,
            "meaningful_change_detected": meaningful,
        }


class SemanticTargetResolver:
    """Resolves UI target elements using a multi-layer strategy."""

    @classmethod
    def resolve_target(cls, state: UIStateModel, target_label: str) -> Optional[UIElementDescriptor]:
        target_lower = target_label.lower()
        # Search structured descriptors first
        for elem in state.elements:
            if target_lower in elem.label.lower():
                return elem
        # Search semantic elements
        for sem in state.semantic_elements:
            if target_lower in sem.label.lower() or target_lower in sem.name.lower() or target_lower in sem.text.lower():
                return UIElementDescriptor(
                    element_id=sem.id,
                    role=sem.role,
                    label=sem.label or sem.name or sem.text,
                    location=sem.bounds,
                    is_enabled=sem.enabled,
                    confidence=PerceptionConfidence.HIGH if sem.confidence >= 0.8 else PerceptionConfidence.MEDIUM,
                )
        return None
