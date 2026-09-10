"""
Screen state comparator for visual verification.
"""

from typing import Optional
from PIL import Image
from jarvis.computer.vision.models import ScreenState, VisualComparisonResult
from jarvis.computer.vision.preprocessing import ImagePreprocessor


class ScreenComparator:
    """
    Compares before/after screen states using lightweight perceptual hashing and OCR diffs.
    """

    @staticmethod
    def compare_images(before_img: Image.Image, after_img: Image.Image) -> VisualComparisonResult:
        """Compares two PIL Images."""
        hash_a = ImagePreprocessor.compute_perceptual_hash(before_img)
        hash_b = ImagePreprocessor.compute_perceptual_hash(after_img)

        diff = ScreenComparator._hamming_distance(hash_a, hash_b)
        changed = diff > 4 # Threshold for noticeable visual change

        return VisualComparisonResult(
            changed=changed,
            perceptual_difference=round(diff / 64.0, 4),
            ocr_difference_count=0,
            description=f"Visual change detected (diff={diff})" if changed else "No visual change detected."
        )

    @staticmethod
    def compare_states(before_state: ScreenState, after_state: ScreenState) -> VisualComparisonResult:
        """Compares two ScreenState objects."""
        if before_state.screen_hash and after_state.screen_hash:
            diff = ScreenComparator._hamming_distance(before_state.screen_hash, after_state.screen_hash)
            changed = diff > 4 or before_state.active_window != after_state.active_window
            return VisualComparisonResult(
                changed=changed,
                perceptual_difference=round(diff / 64.0, 4),
                ocr_difference_count=abs(len(before_state.ocr_regions) - len(after_state.ocr_regions)),
                description=f"Screen state changed. Active window: '{before_state.active_window}' -> '{after_state.active_window}'"
            )

        changed = before_state.visual_summary != after_state.visual_summary
        return VisualComparisonResult(
            changed=changed,
            perceptual_difference=0.5 if changed else 0.0,
            ocr_difference_count=0,
            description="Visual summary changed." if changed else "No visual summary change."
        )

    @staticmethod
    def _hamming_distance(hash1: str, hash2: str) -> int:
        if not hash1 or not hash2 or len(hash1) != len(hash2):
            return 64
        try:
            val1 = int(hash1, 16)
            val2 = int(hash2, 16)
            return bin(val1 ^ val2).count("1")
        except ValueError:
            return 64
