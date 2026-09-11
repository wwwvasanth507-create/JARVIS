"""
Unit tests for SemanticComputerInteractor and TargetLease.
"""

import pytest
from jarvis.computer.semantic_interactor import SemanticComputerInteractor
from jarvis.computer.vision.target_query import TargetQuery
from jarvis.computer.vision.ui_element import UIElement, PerceptionSource


def test_semantic_interactor_find_and_click():
    interactor = SemanticComputerInteractor.get_instance()
    snap = interactor.capture_snapshot()
    assert snap is not None
    assert len(snap.elements) > 0

    q = TargetQuery(name="Submit", role="button")
    elem = interactor.find_element(q)
    assert elem is not None
    assert "Submit" in elem.name or "Submit" in elem.label

    res = interactor.click_element(q)
    assert res.success is True
    assert res.lease_id is not None


def test_semantic_interactor_type_and_wait():
    interactor = SemanticComputerInteractor.get_instance()
    q = TargetQuery(name="Search", role="input")
    res_type = interactor.type_into_element(q, "Testing JARVIS")
    assert res_type.success is True

    res_wait = interactor.wait_for_element(TargetQuery(name="Submit"), timeout_sec=2.0)
    assert res_wait.success is True
