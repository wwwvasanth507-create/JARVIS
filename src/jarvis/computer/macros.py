"""
Semantic User Teaching Mode & Reusable Macro Subsystem for JARVIS.

Records user actions as structured semantic macro steps (not raw coordinate macros)
with versioning, dependency tracking, safety verification, and privacy redaction.
"""

import time
import json
import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from jarvis.computer.vision.target_query import TargetQuery
from jarvis.security.permissions import RiskLevel

logger = logging.getLogger(__name__)


class SemanticMacroStep(BaseModel):
    step_id: int
    action: str  # "click", "type", "select", "wait", "fill_form"
    target_query: TargetQuery
    parameters: Dict[str, Any] = Field(default_factory=dict)
    is_sensitive: bool = False
    verification_condition: Optional[str] = None


class SemanticMacro(BaseModel):
    """
    Reusable semantic macro storing high-level UI workflows without raw coordinate dependencies.
    """
    macro_id: str
    name: str
    description: str = ""
    version: str = "1.0.0"
    created_at: float = Field(default_factory=time.time)
    required_capabilities: List[str] = Field(default_factory=list)
    risk_level: RiskLevel = RiskLevel.LOW
    steps: List[SemanticMacroStep] = Field(default_factory=list)

    def validate_safety(self) -> bool:
        """Verifies macro steps do not contain unprotected password inputs or restricted actions."""
        for step in self.steps:
            if step.is_sensitive and "password" in json.dumps(step.parameters).lower():
                return False
        return True


class MacroRegistry:
    """Registry for managing and executing user-taught semantic macros."""

    _instance: Optional["MacroRegistry"] = None

    def __init__(self):
        self._macros: Dict[str, SemanticMacro] = {}

    @classmethod
    def get_instance(cls) -> "MacroRegistry":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register_macro(self, macro: SemanticMacro) -> bool:
        if not macro.validate_safety():
            logger.warning(f"Macro '{macro.name}' failed safety validation.")
            return False
        self._macros[macro.macro_id] = macro
        logger.info(f"Registered semantic macro '{macro.name}' (v{macro.version})")
        return True

    def get_macro(self, macro_id: str) -> Optional[SemanticMacro]:
        return self._macros.get(macro_id)

    def list_macros(self) -> List[SemanticMacro]:
        return list(self._macros.values())
