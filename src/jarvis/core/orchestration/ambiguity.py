"""
First-Class Ambiguity & Targeted Clarification Handler for JARVIS Orchestration.

Surfaces structured clarification questions ("I found 3 matching files: X, Y, Z. Which one should I open, Boss?")
rather than silently guessing among materially different targets.
"""

from enum import Enum
from pathlib import Path
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from jarvis.core.orchestration.conversation_state import ConversationStateManager

logger = logging.getLogger(__name__)


class AmbiguityType(str, Enum):
    MULTIPLE_FILES = "MULTIPLE_FILES"
    MULTIPLE_APPLICATIONS = "MULTIPLE_APPLICATIONS"
    MULTIPLE_WINDOW_TABS = "MULTIPLE_WINDOW_TABS"
    MISSING_PARAMETER = "MISSING_PARAMETER"
    CONFRACTORY_INTENT = "CONFRACTORY_INTENT"


class AmbiguityCandidate(BaseModel):
    label: str
    target_value: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class StructuredAmbiguity(BaseModel):
    ambiguity_type: AmbiguityType
    question: str
    candidates: List[AmbiguityCandidate] = Field(default_factory=list)
    confidence: float = 0.5
    reason: str = ""
    context: Dict[str, Any] = Field(default_factory=dict)


class AmbiguityHandler:
    """Detects multi-candidate ambiguity and generates structured clarification requests."""

    def __init__(self, state_mgr: Optional[ConversationStateManager] = None):
        self.state_mgr = state_mgr or ConversationStateManager.get_instance()

    def check_file_search_ambiguity(self, search_pattern: str, candidates: List[str]) -> Optional[StructuredAmbiguity]:
        """Checks if a file search produced multiple candidate matches requiring Boss decision."""
        if len(candidates) <= 1:
            return None

        # Build candidate objects
        cand_objs = [
            AmbiguityCandidate(label=Path(c).name if "/" in c or "\\" in c else c, target_value=c)
            for c in candidates[:5]
        ]
        cand_names = [c.label for c in cand_objs]
        
        question = f"I found {len(candidates)} matching files for '{search_pattern}': {', '.join(cand_names)}. Which one should I open, Boss?"

        amb = StructuredAmbiguity(
            ambiguity_type=AmbiguityType.MULTIPLE_FILES,
            question=question,
            candidates=cand_objs,
            confidence=0.4,
            reason=f"Multiple files match search pattern '{search_pattern}'",
            context={"pattern": search_pattern, "candidates": candidates}
        )

        # Store pending clarification in conversation state
        self.state_mgr.state.pending_clarification = amb.model_dump()
        logger.info(f"AmbiguityHandler detected {len(candidates)} candidate files for '{search_pattern}'. Created clarification.")
        return amb

    def check_application_ambiguity(self, app_name: str, matches: List[str]) -> Optional[StructuredAmbiguity]:
        if len(matches) <= 1:
            return None

        cand_objs = [AmbiguityCandidate(label=m, target_value=m) for m in matches[:5]]
        question = f"I found {len(matches)} matching applications for '{app_name}': {', '.join(matches)}. Which one would you like to launch, Boss?"

        amb = StructuredAmbiguity(
            ambiguity_type=AmbiguityType.MULTIPLE_APPLICATIONS,
            question=question,
            candidates=cand_objs,
            confidence=0.4,
            reason=f"Multiple applications match '{app_name}'",
            context={"app_name": app_name, "candidates": matches}
        )
        self.state_mgr.state.pending_clarification = amb.model_dump()
        return amb

    def has_pending_clarification(self) -> bool:
        return self.state_mgr.state.pending_clarification is not None

    def store_pending_clarification(self, ambiguity: StructuredAmbiguity) -> None:
        self.state_mgr.state.pending_clarification = ambiguity.model_dump()

    def resolve_pending_clarification(self, user_answer: str) -> Optional[AmbiguityCandidate]:
        """
        Resolves pending clarification against user's answer ("the second one", "Downloads/report.pdf").
        Returns concrete selected AmbiguityCandidate if resolved, or None.
        """
        pending = self.state_mgr.state.pending_clarification
        if not pending:
            return None

        candidates = pending.get("candidates", [])
        answer_lower = user_answer.strip().lower()

        # 1. Check ordinal selection ("the first one", "second")
        from jarvis.core.orchestration.reference_resolver import ReferenceResolver
        rr = ReferenceResolver(self.state_mgr)
        ord_idx = rr._extract_ordinal_index(user_answer)
        if ord_idx is not None and len(candidates) > ord_idx:
            cand = candidates[ord_idx]
            if isinstance(cand, dict):
                selected = AmbiguityCandidate(**cand)
            else:
                selected = AmbiguityCandidate(label=str(cand), target_value=str(cand))
            self.state_mgr.state.pending_clarification = None
            return selected

        # 2. Check exact or partial label matching
        for cand in candidates:
            if isinstance(cand, dict):
                cand_obj = AmbiguityCandidate(**cand)
            else:
                cand_obj = AmbiguityCandidate(label=str(cand), target_value=str(cand))

            label = cand_obj.label.lower()
            val = cand_obj.target_value.lower()
            if answer_lower in label or label in answer_lower or answer_lower in val:
                self.state_mgr.state.pending_clarification = None
                return cand_obj

        return None
