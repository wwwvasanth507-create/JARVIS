"""
Structured Target Query and Relationship Definitions for JARVIS.
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class TargetRelation(str, Enum):
    ABOVE = "above"
    BELOW = "below"
    LEFT_OF = "left_of"
    RIGHT_OF = "right_of"
    NEAR = "near"
    INSIDE = "inside"
    CONTAINS = "contains"
    NEXT_TO = "next_to"
    BEFORE = "before"
    AFTER = "after"
    SAME_ROW = "same_row"
    SAME_COLUMN = "same_column"


class TargetQuery(BaseModel):
    """
    Structured query for finding UI elements in snapshots without relying solely on coordinates.
    """
    role: Optional[str] = None
    name: Optional[str] = None
    label: Optional[str] = None
    text: Optional[str] = None
    placeholder: Optional[str] = None
    contains_text: Optional[str] = None
    relation: Optional[TargetRelation] = None
    relative_to_label: Optional[str] = None
    relative_to_role: Optional[str] = None
    container: Optional[str] = None
    application: Optional[str] = None
    window: Optional[str] = None
    region: Optional[str] = None
    index: Optional[int] = None  # 0-indexed or 1-indexed (e.g. 3rd option)
    min_confidence: float = 0.3

    @classmethod
    def from_text(cls, text: str, role: Optional[str] = None) -> "TargetQuery":
        """Convenience constructor from text string."""
        return cls(name=text, label=text, text=text, contains_text=text, role=role)
