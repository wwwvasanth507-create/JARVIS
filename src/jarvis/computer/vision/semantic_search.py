"""
Ranked Semantic Element Search and Spatial Relationship Resolver for JARVIS.
"""

import math
import logging
from typing import List, Optional, Tuple, Dict, Any
from jarvis.computer.vision.ui_element import UIElement, PerceptionSource, SOURCE_CONFIDENCE_WEIGHTS
from jarvis.computer.vision.target_query import TargetQuery, TargetRelation
from jarvis.computer.vision.snapshot import ScreenSemanticSnapshot

logger = logging.getLogger(__name__)


class AmbiguousTargetError(Exception):
    """Raised when multiple UI elements match a query with high confidence ambiguity."""
    def __init__(self, message: str, matches: List[UIElement]):
        super().__init__(message)
        self.matches = matches


class SemanticSearchEngine:
    """
    Ranks UI elements by role, accessible name, label, text, application context,
    spatial relations, geometric constraints, source reliability, and confidence.
    """

    @classmethod
    def search(
        cls,
        snapshot: ScreenSemanticSnapshot,
        query: TargetQuery,
        disambiguate: bool = False
    ) -> List[UIElement]:
        """
        Executes a ranked search for elements matching query.
        Returns sorted matches in descending order of relevance score.
        """
        # 1. First find anchor element if relation is spatial
        anchor_elem: Optional[UIElement] = None
        if query.relation and (query.relative_to_label or query.relative_to_role):
            anchor_query = TargetQuery(
                name=query.relative_to_label,
                label=query.relative_to_label,
                text=query.relative_to_label,
                role=query.relative_to_role,
            )
            anchor_matches = cls.search(snapshot, anchor_query, disambiguate=False)
            if anchor_matches:
                anchor_elem = anchor_matches[0]

        candidates: List[Tuple[float, UIElement]] = []

        # 2. Score each element in snapshot
        for elem in snapshot.elements:
            score = cls._score_element(elem, query, anchor_elem)
            if score >= query.min_confidence:
                candidates.append((score, elem))

        # Sort candidates by score descending
        candidates.sort(key=lambda x: x[0], reverse=True)
        results = [elem for score, elem in candidates]

        # Handle index selector if provided (e.g. 3rd option)
        if query.index is not None and results:
            idx = query.index if query.index < len(results) else -1
            if idx >= 0:
                results = [results[idx]]

        # Raise AmbiguousTargetError if disambiguate is True and ambiguity exists
        if disambiguate and len(candidates) > 1:
            top_score = candidates[0][0]
            second_score = candidates[1][0]
            if abs(top_score - second_score) < 0.05 and top_score > 0.6:
                if candidates[0][1].name.lower() == candidates[1][1].name.lower():
                    raise AmbiguousTargetError(
                        f"Found {len(candidates)} matching elements for '{query.name or query.role}'",
                        matches=[c[1] for c in candidates[:3]]
                    )

        return results

    @classmethod
    def _score_element(cls, elem: UIElement, query: TargetQuery, anchor: Optional[UIElement]) -> float:
        score = 0.0

        # Base confidence from source
        eff_conf = elem.get_effective_confidence()
        score += eff_conf * 0.3

        # Role match
        if query.role:
            if elem.role.lower() == query.role.lower():
                score += 0.25
            elif query.role.lower() in elem.role.lower():
                score += 0.15
            else:
                score -= 0.1  # Role mismatch penalty

        # Exact text / name / label match
        target_text = (query.name or query.label or query.text or "").lower().strip()
        if target_text:
            elem_name = (elem.name or "").lower().strip()
            elem_label = (elem.label or "").lower().strip()
            elem_text = (elem.text or "").lower().strip()
            elem_val = (elem.value or "").lower().strip()
            elem_ph = (elem.placeholder or "").lower().strip()

            if target_text in (elem_name, elem_label, elem_text):
                score += 0.35
            elif target_text in (elem_val, elem_ph):
                score += 0.25
            elif target_text in elem_name or target_text in elem_label or target_text in elem_text:
                score += 0.20
            elif query.contains_text and query.contains_text.lower() in (elem_name + elem_label + elem_text):
                score += 0.15

        # Container / Region / Window check
        if query.container and elem.container:
            if query.container.lower() in elem.container.lower():
                score += 0.1
        if query.window and elem.window:
            if query.window.lower() in elem.window.lower():
                score += 0.05

        # Spatial / Relational evaluation
        if query.relation and anchor:
            rel_score = cls._eval_spatial_relation(elem, anchor, query.relation)
            if rel_score <= 0.0:
                return 0.0  # Fails spatial condition strictly
            score += rel_score * 0.3

        return min(1.0, round(score, 3))

    @classmethod
    def _eval_spatial_relation(cls, elem: UIElement, anchor: UIElement, relation: TargetRelation) -> float:
        e_c = elem.center_point()
        a_c = anchor.center_point()

        if not e_c or not a_c:
            return 0.5  # Fallback neutral score if bounds unavailable

        dx = e_c["x"] - a_c["x"]
        dy = e_c["y"] - a_c["y"]
        dist = math.hypot(dx, dy)

        if relation in (TargetRelation.RIGHT_OF, TargetRelation.NEXT_TO, TargetRelation.AFTER):
            if dx > 0 and abs(dy) < 80:
                return 1.0 - min(1.0, dist / 800.0)
            if relation == TargetRelation.NEXT_TO and abs(dx) < 150 and abs(dy) < 60:
                return 0.9

        if relation in (TargetRelation.LEFT_OF, TargetRelation.BEFORE):
            if dx < 0 and abs(dy) < 80:
                return 1.0 - min(1.0, dist / 800.0)

        if relation == TargetRelation.BELOW:
            if dy > 0 and abs(dx) < 120:
                return 1.0 - min(1.0, dist / 600.0)

        if relation == TargetRelation.ABOVE:
            if dy < 0 and abs(dx) < 120:
                return 1.0 - min(1.0, dist / 600.0)

        if relation == TargetRelation.SAME_ROW:
            if abs(dy) < 30:
                return 1.0

        if relation == TargetRelation.SAME_COLUMN:
            if abs(dx) < 40:
                return 1.0

        if relation == TargetRelation.NEAR:
            return 1.0 - min(1.0, dist / 500.0)

        if relation == TargetRelation.INSIDE or relation == TargetRelation.CONTAINS:
            return 0.8

        return 0.0
