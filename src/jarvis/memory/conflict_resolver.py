"""
Memory Conflict Engine for JARVIS.

Resolves fact and preference conflicts across memory items, recency, source trust,
and scope precedence matrix:
`current explicit instruction > task scope > project scope > application scope > global preference > weak inference`.
"""

import logging
from typing import List, Dict, Any, Optional
from jarvis.memory.memory_layers import ScopedPreference, MemoryScope, MemorySource, PreferenceLevel, SOURCE_TRUST_WEIGHTS

logger = logging.getLogger(__name__)


class MemoryConflictResolver:
    """
    Resolves conflicting preferences and facts deterministically.
    Current verified observations and explicit user instructions ALWAYS override historical memories.
    """

    SCOPE_PRECEDENCE: Dict[MemoryScope, int] = {
        MemoryScope.WORKFLOW: 6,
        MemoryScope.TASK: 5,
        MemoryScope.SESSION: 4,
        MemoryScope.PROJECT: 3,
        MemoryScope.APPLICATION: 2,
        MemoryScope.GLOBAL: 1,
    }

    @classmethod
    def resolve_preference_conflict(
        cls,
        candidates: List[ScopedPreference],
        active_scope: Optional[MemoryScope] = None
    ) -> Optional[ScopedPreference]:
        """
        Selects winning preference using scope, source trust, recency, and explicit vs inferred level.
        """
        if not candidates:
            return None
        if len(candidates) == 1:
            return candidates[0]

        def sort_key(pref: ScopedPreference) -> tuple:
            # 1. Level: EXPLICIT (3) > STRONG_INFERENCE (2) > WEAK_INFERENCE (1)
            level_score = 3 if pref.level == PreferenceLevel.EXPLICIT else (2 if pref.level == PreferenceLevel.STRONG_INFERENCE else 1)
            # 2. Scope precedence score
            scope_score = cls.SCOPE_PRECEDENCE.get(pref.scope, 1)
            # 3. Source trust weight
            source_weight = SOURCE_TRUST_WEIGHTS.get(pref.source, 0.5)
            # 4. Decayed confidence
            eff_conf = pref.get_decayed_confidence()
            # 5. Recency (updated_at)
            recency = pref.updated_at

            return (level_score, scope_score, source_weight, eff_conf, recency)

        sorted_prefs = sorted(candidates, key=sort_key, reverse=True)
        winner = sorted_prefs[0]
        logger.info(f"ConflictResolver selected '{winner.key}={winner.value}' (Scope: {winner.scope.value}, Level: {winner.level.value})")
        return winner
