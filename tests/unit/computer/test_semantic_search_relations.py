"""
Unit tests for SemanticSearchEngine, spatial relations, confidence ranking, and ambiguity handling.
"""

import pytest
from jarvis.computer.vision.ui_element import UIElement, PerceptionSource
from jarvis.computer.vision.target_query import TargetQuery, TargetRelation
from jarvis.computer.vision.snapshot import ScreenSemanticSnapshot
from jarvis.computer.vision.semantic_search import SemanticSearchEngine, AmbiguousTargetError


def test_spatial_relation_right_of():
    adv_elem = UIElement(id="e1", role="button", name="Advanced", bounds={"x": 100, "y": 50, "width": 100, "height": 30})
    dl_elem = UIElement(id="e2", role="button", name="Download", bounds={"x": 220, "y": 50, "width": 80, "height": 30})
    snap = ScreenSemanticSnapshot(elements=[adv_elem, dl_elem])

    q = TargetQuery(name="Download", relation=TargetRelation.RIGHT_OF, relative_to_label="Advanced")
    matches = SemanticSearchEngine.search(snap, q)
    assert len(matches) > 0
    assert matches[0].id == "e2"


def test_source_confidence_precedence():
    elem_ocr = UIElement(id="ocr_1", role="button", name="Submit", source=PerceptionSource.OCR, confidence=0.90)
    elem_dom = UIElement(id="dom_1", role="button", name="Submit", source=PerceptionSource.DOM, confidence=0.95)
    snap = ScreenSemanticSnapshot(elements=[elem_ocr, elem_dom])

    q = TargetQuery(name="Submit")
    matches = SemanticSearchEngine.search(snap, q)
    assert matches[0].source == PerceptionSource.DOM


def test_ambiguity_detection():
    btn1 = UIElement(id="b1", role="button", name="Submit", source=PerceptionSource.DOM, confidence=0.95)
    btn2 = UIElement(id="b2", role="button", name="Submit", source=PerceptionSource.DOM, confidence=0.95)
    snap = ScreenSemanticSnapshot(elements=[btn1, btn2])

    q = TargetQuery(name="Submit")
    with pytest.raises(AmbiguousTargetError):
        SemanticSearchEngine.search(snap, q, disambiguate=True)
