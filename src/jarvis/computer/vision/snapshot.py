"""
Screen Semantic Snapshot Model for Structured UI State.
"""

import time
import hashlib
import json
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from jarvis.computer.vision.ui_element import UIElement


class ScreenSemanticSnapshot(BaseModel):
    """
    Structured snapshot of application / screen state containing semantic elements,
    regions, dialogs, forms, tables, loading state, and active metadata.
    """
    application: str = "Unknown"
    window: str = ""
    url: Optional[str] = None
    elements: List[UIElement] = Field(default_factory=list)
    regions: Dict[str, List[UIElement]] = Field(default_factory=dict)  # e.g. "header", "sidebar", "main", "dialog", "table", "form"
    dialogs: List[Dict[str, Any]] = Field(default_factory=list)
    forms: List[Dict[str, Any]] = Field(default_factory=list)
    tables: List[Dict[str, Any]] = Field(default_factory=list)
    visible_text: str = ""
    selected_element: Optional[UIElement] = None
    focused_element: Optional[UIElement] = None
    loading_state: bool = False
    confidence: float = 0.95
    timestamp: float = Field(default_factory=time.time)

    def compute_state_hash(self) -> str:
        """Computes deterministic hash representing current semantic state."""
        payload = f"{self.application}:{self.window}:{self.url}:{self.loading_state}:{len(self.elements)}:{len(self.dialogs)}"
        elem_summary = "-".join([f"{e.role}:{e.name}:{e.value}" for e in self.elements[:10]])
        full = f"{payload}:{elem_summary}"
        return hashlib.sha256(full.encode()).hexdigest()[:16]
