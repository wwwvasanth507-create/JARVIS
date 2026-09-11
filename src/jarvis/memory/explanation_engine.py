"""
Memory Explanation Engine for JARVIS.

Provides human-readable and structured explanations for why a memory exists,
its source provenance, last updated timestamp, confidence level, and retrieval justification.
"""

import time
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

from jarvis.memory.models import MemoryItem
from jarvis.memory.memory_layers import MemorySource, ScopedPreference


class MemoryExplanation(BaseModel):
    memory_id: str
    key: str
    content: str
    source: str
    confidence: str
    created_at_formatted: str
    updated_at_formatted: str
    explanation: str
    provenance_details: Dict[str, Any] = Field(default_factory=dict)


class MemoryExplanationEngine:
    """
    Generates deterministic provenance explanations for stored memory items and preferences.
    """

    @classmethod
    def explain_memory(cls, item: MemoryItem) -> MemoryExplanation:
        created_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(item.created_at))
        updated_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(item.updated_at))

        source_desc = {
            "USER_EXPLICIT": "explicitly told to me by you",
            "USER_CORRECTED": "corrected by you after a previous mistake",
            "TOOL_VERIFIED": "verified via automated tool execution",
            "TASK_OUTCOME": "learned from a successful task outcome",
            "SYSTEM_OBSERVED": "observed from system environment state",
            "INFERRED": "inferred from repeated usage patterns",
            "EXTERNAL_CONTENT": "extracted from external document/web payload",
        }.get(item.source, "recorded during system operation")

        explanation_text = (
            f"This memory ('{item.key}') was {source_desc} on {created_str}. "
            f"Confidence level is {item.confidence.value if hasattr(item.confidence, 'value') else item.confidence}."
        )

        return MemoryExplanation(
            memory_id=item.id,
            key=item.key,
            content=item.content,
            source=item.source,
            confidence=str(item.confidence),
            created_at_formatted=created_str,
            updated_at_formatted=updated_str,
            explanation=explanation_text,
            provenance_details={
                "privacy_level": item.privacy_level,
                "importance": item.importance,
                "access_count": item.access_count,
            },
        )

    @classmethod
    def explain_preference(cls, pref: ScopedPreference) -> MemoryExplanation:
        created_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(pref.created_at))
        updated_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(pref.updated_at))

        explanation_text = (
            f"You have a stored preference '{pref.key}={pref.value}' at {pref.scope.value} scope. "
            f"Source is {pref.source.value} ({pref.level.value})."
        )

        return MemoryExplanation(
            memory_id=f"pref_{pref.key}",
            key=pref.key,
            content=str(pref.value),
            source=pref.source.value,
            confidence=f"{pref.get_decayed_confidence()*100:.1f}%",
            created_at_formatted=created_str,
            updated_at_formatted=updated_str,
            explanation=explanation_text,
            provenance_details={
                "scope": pref.scope.value,
                "level": pref.level.value,
                "decayed_confidence": pref.get_decayed_confidence(),
            },
        )
