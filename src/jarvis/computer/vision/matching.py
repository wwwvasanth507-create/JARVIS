"""
Visual target matching and ambiguity detection.
"""

from typing import List, Optional
from jarvis.computer.vision.models import VisualElement, VisualTarget
from jarvis.computer.vision.errors import VisualTargetNotFoundError, AmbiguousVisualTargetError


class VisualTargetMatcher:
    """
    Finds matching VisualElement for a given VisualTarget.
    Raises AmbiguousVisualTargetError if multiple candidates meet confidence threshold.
    """

    def find_target(
        self,
        target: VisualTarget,
        elements: List[VisualElement]
    ) -> VisualElement:
        """
        Finds exact matching element or raises exception.
        """
        matches = []
        target_text = (target.text or target.description).lower()

        for elem in elements:
            if elem.confidence < target.confidence_threshold:
                continue

            elem_label = elem.label.lower()
            if target_text in elem_label or elem_label in target_text:
                if target.element_type == target.element_type.UNKNOWN or elem.type == target.element_type:
                    matches.append(elem)

        if not matches:
            raise VisualTargetNotFoundError(
                f"VISUAL_TARGET_NOT_FOUND: No visual element found matching '{target.description}'."
            )

        if len(matches) > 1:
            # If multiple candidates have exact identical high confidence label match
            match_labels = [m.label for m in matches]
            raise AmbiguousVisualTargetError(
                f"AMBIGUOUS_VISUAL_TARGET: Found {len(matches)} matching targets for '{target.description}': {match_labels}"
            )

        return matches[0]
