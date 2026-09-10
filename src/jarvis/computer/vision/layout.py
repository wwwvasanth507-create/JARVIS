"""
Spatial layout analysis for visual elements.
"""

from typing import List, Dict, Any, Optional
from jarvis.computer.vision.models import VisualElement


class LayoutAnalyzer:
    """
    Analyzes spatial relations (above, below, left_of, right_of) between detected visual elements.
    """

    @staticmethod
    def find_element_near(
        target_label: str,
        elements: List[VisualElement],
        direction: str = "any" # any, left, right, above, below
    ) -> Optional[VisualElement]:
        target_lower = target_label.lower()
        anchor = None

        for elem in elements:
            if target_lower in elem.label.lower():
                anchor = elem
                break

        if not anchor:
            return None

        if direction == "any":
            return anchor

        # Find closest candidate matching direction
        candidates = []
        for elem in elements:
            if elem.element_id == anchor.element_id:
                continue

            dx = elem.x - anchor.x
            dy = elem.y - anchor.y

            if direction == "right" and dx > 0 and abs(dy) < 50:
                candidates.append((dx, elem))
            elif direction == "left" and dx < 0 and abs(dy) < 50:
                candidates.append((abs(dx), elem))
            elif direction == "below" and dy > 0 and abs(dx) < 100:
                candidates.append((dy, elem))
            elif direction == "above" and dy < 0 and abs(dx) < 100:
                candidates.append((abs(dy), elem))

        if candidates:
            candidates.sort(key=lambda c: c[0])
            return candidates[0][1]

        return None
