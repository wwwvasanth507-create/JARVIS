"""Unit tests for BaseApplicationSemanticAdapter, UIStateDiffEngine, and ObservationCache."""

import pytest
from jarvis.applications.application_semantics import BaseApplicationSemanticAdapter, ApplicationFamily
from jarvis.computer.vision.ui_state_model import UIStateModel, UIElementDescriptor, UIStateDiffEngine, SemanticTargetResolver, PerceptionConfidence
from jarvis.core.orchestration.observation_cache import ObservationCache


def test_application_semantics_family_inference():
    adapter = BaseApplicationSemanticAdapter()

    chrome_state = adapter.observe_semantics("chrome.exe", "Google Search - Google Chrome")
    assert chrome_state.family == ApplicationFamily.WEB_BROWSER

    code_state = adapter.observe_semantics("code.exe", "* main.py - Visual Studio Code")
    assert code_state.family == ApplicationFamily.TEXT_EDITOR
    assert code_state.has_unsaved_changes is True


def test_ui_state_diff_and_target_resolver():
    elem = UIElementDescriptor(element_id="btn_1", role="button", label="Submit Order", confidence=PerceptionConfidence.HIGH)
    state1 = UIStateModel(active_application="Chrome", window_title="Checkout", elements=[elem])
    state2 = UIStateModel(active_application="Chrome", window_title="Order Confirmed", elements=[], dialog_present=True)

    diff = UIStateDiffEngine.compute_diff(state1, state2)
    assert diff["meaningful_change_detected"] is True
    assert diff["dialog_appeared"] is True

    resolved = SemanticTargetResolver.resolve_target(state1, "Submit")
    assert resolved is not None
    assert resolved.element_id == "btn_1"


def test_observation_cache_freshness():
    cache = ObservationCache()
    cache.put("key_1", {"data": "test_value"}, ttl_sec=1.0)

    assert cache.get("key_1") == {"data": "test_value"}
    assert cache.requires_reobservation("filesystem.delete", "key_1") is False
