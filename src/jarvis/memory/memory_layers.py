"""
6-Layer Memory Architecture definitions, Sources, Scopes, and Preferences for JARVIS.
"""

from enum import Enum
import time
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class MemoryLayer(str, Enum):
    WORKING = "WORKING"
    EPISODIC = "EPISODIC"
    SEMANTIC = "SEMANTIC"
    PREFERENCE = "PREFERENCE"
    PROJECT = "PROJECT"
    KNOWLEDGE = "KNOWLEDGE"


class MemorySource(str, Enum):
    USER_EXPLICIT = "USER_EXPLICIT"
    TOOL_VERIFIED = "TOOL_VERIFIED"
    SYSTEM_OBSERVED = "SYSTEM_OBSERVED"
    TASK_OUTCOME = "TASK_OUTCOME"
    USER_CORRECTED = "USER_CORRECTED"
    INFERRED = "INFERRED"
    EXTERNAL_CONTENT = "EXTERNAL_CONTENT"


SOURCE_TRUST_WEIGHTS: Dict[MemorySource, float] = {
    MemorySource.USER_CORRECTED: 1.0,
    MemorySource.USER_EXPLICIT: 0.98,
    MemorySource.TOOL_VERIFIED: 0.90,
    MemorySource.TASK_OUTCOME: 0.85,
    MemorySource.SYSTEM_OBSERVED: 0.70,
    MemorySource.INFERRED: 0.50,
    MemorySource.EXTERNAL_CONTENT: 0.30,  # Untrusted external payload
}


class PreferenceLevel(str, Enum):
    EXPLICIT = "EXPLICIT"
    STRONG_INFERENCE = "STRONG_INFERENCE"
    WEAK_INFERENCE = "WEAK_INFERENCE"


class MemoryScope(str, Enum):
    GLOBAL = "GLOBAL"
    PROJECT = "PROJECT"
    TASK = "TASK"
    SESSION = "SESSION"
    APPLICATION = "APPLICATION"
    WORKFLOW = "WORKFLOW"


class ScopedPreference(BaseModel):
    key: str
    value: Any
    level: PreferenceLevel = PreferenceLevel.EXPLICIT
    scope: MemoryScope = MemoryScope.GLOBAL
    scope_id: Optional[str] = None  # e.g. project_id or app_name
    source: MemorySource = MemorySource.USER_EXPLICIT
    confidence: float = 1.0
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)
    expires_at: Optional[float] = None

    def get_decayed_confidence(self, half_life_days: float = 30.0) -> float:
        """
        Calculates decayed confidence for inferred preferences over time.
        Explicit user preferences NEVER silently decay.
        """
        if self.level == PreferenceLevel.EXPLICIT:
            return self.confidence

        elapsed_days = (time.time() - self.updated_at) / 86400.0
        decay_factor = 0.5 ** (elapsed_days / half_life_days)
        return round(self.confidence * decay_factor, 3)
