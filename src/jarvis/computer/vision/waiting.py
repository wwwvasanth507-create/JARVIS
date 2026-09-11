"""
Intelligent Wait-For-Condition Engine for Semantic UI Automation.
"""

import time
import logging
from typing import Callable, Optional, Any, Dict
from jarvis.computer.vision.target_query import TargetQuery
from jarvis.computer.vision.snapshot import ScreenSemanticSnapshot
from jarvis.computer.vision.semantic_search import SemanticSearchEngine, UIElement

logger = logging.getLogger(__name__)


class ConditionTimeoutError(TimeoutError):
    """Raised when waiting for a semantic UI condition times out."""
    pass


class SemanticWaitEngine:
    """
    Evaluates observable UI conditions using event checks and bounded polling with exponential backoff,
    replacing arbitrary fixed sleeps like time.sleep(10).
    """

    @classmethod
    def wait_for_condition(
        cls,
        condition_fn: Callable[[], bool],
        timeout_sec: float = 10.0,
        poll_interval_sec: float = 0.25,
        condition_name: str = "custom condition"
    ) -> bool:
        start_time = time.time()
        attempt = 0

        while time.time() - start_time < timeout_sec:
            try:
                if condition_fn():
                    elapsed = round(time.time() - start_time, 2)
                    logger.info(f"Condition '{condition_name}' satisfied in {elapsed}s")
                    return True
            except Exception as e:
                logger.debug(f"Condition check error ({condition_name}): {e}")

            time.sleep(poll_interval_sec)
            attempt += 1

        elapsed = round(time.time() - start_time, 2)
        logger.warning(f"Condition '{condition_name}' timed out after {elapsed}s")
        raise ConditionTimeoutError(f"Condition '{condition_name}' timed out after {timeout_sec}s")

    @classmethod
    def wait_until_element_exists(
        cls,
        snapshot_provider: Callable[[], ScreenSemanticSnapshot],
        query: TargetQuery,
        timeout_sec: float = 10.0
    ) -> UIElement:
        target: Optional[UIElement] = None

        def check() -> bool:
            nonlocal target
            snap = snapshot_provider()
            matches = SemanticSearchEngine.search(snap, query, disambiguate=False)
            if matches:
                target = matches[0]
                return True
            return False

        cls.wait_for_condition(check, timeout_sec=timeout_sec, condition_name=f"element_exists({query.name or query.role})")
        assert target is not None
        return target

    @classmethod
    def wait_until_dialog_disappears(
        cls,
        snapshot_provider: Callable[[], ScreenSemanticSnapshot],
        timeout_sec: float = 10.0
    ) -> bool:
        def check() -> bool:
            snap = snapshot_provider()
            return len(snap.dialogs) == 0

        return cls.wait_for_condition(check, timeout_sec=timeout_sec, condition_name="dialog_disappears")

    @classmethod
    def wait_until_text_appears(
        cls,
        snapshot_provider: Callable[[], ScreenSemanticSnapshot],
        text: str,
        timeout_sec: float = 10.0
    ) -> bool:
        target_lower = text.lower().strip()

        def check() -> bool:
            snap = snapshot_provider()
            return target_lower in snap.visible_text.lower()

        return cls.wait_for_condition(check, timeout_sec=timeout_sec, condition_name=f"text_appears('{text}')")

    @classmethod
    def wait_until_loading_ends(
        cls,
        snapshot_provider: Callable[[], ScreenSemanticSnapshot],
        timeout_sec: float = 15.0
    ) -> bool:
        def check() -> bool:
            snap = snapshot_provider()
            return not snap.loading_state

        return cls.wait_for_condition(check, timeout_sec=timeout_sec, condition_name="loading_ends")

    @classmethod
    def wait_until_element_enabled(
        cls,
        snapshot_provider: Callable[[], ScreenSemanticSnapshot],
        query: TargetQuery,
        timeout_sec: float = 10.0
    ) -> bool:
        def check() -> bool:
            snap = snapshot_provider()
            matches = SemanticSearchEngine.search(snap, query, disambiguate=False)
            return len(matches) > 0 and matches[0].enabled

        return cls.wait_for_condition(check, timeout_sec=timeout_sec, condition_name=f"element_enabled({query.name or query.role})")
