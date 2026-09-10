"""
Unit tests for DocumentSummarizer and DocumentAnalyzer.
"""

import pytest
import os
import tempfile
from jarvis.documents.manager import DocumentManager


def test_document_summarization():
    mgr = DocumentManager()
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as tmp:
        tmp.write("# Financial Overview\nRevenue grew by 18% in Q3 due to strong sales.")
        tmp_path = tmp.name

    try:
        summary = mgr.summarize_document(tmp_path)
        assert "Overview" in summary.summary_text or "Financial" in summary.summary_text
        assert summary.document_id.startswith("doc_")
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_document_analyzer_qa_source_grounding():
    mgr = DocumentManager()
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as tmp:
        tmp.write("# Revenue Report\n\nRevenue increased by 18% year over year in Q4.\n\n# Expenses Report\nExpenses were reduced by 5%.")
        tmp_path = tmp.name

    try:
        ans = mgr.ask_document("What does this report say about revenue?", tmp_path)
        assert ans.answer is not None
        assert len(ans.sources) > 0
        assert ans.sources[0]["section"] == "Revenue Report"
        assert "18%" in ans.answer or "increased" in ans.answer
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_document_search():
    mgr = DocumentManager()
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as tmp:
        tmp.write("Line 1: Normal line\nLine 2: Target keyword database.host\nLine 3: End")
        tmp_path = tmp.name

    try:
        results = mgr.search_document("database.host", tmp_path)
        assert len(results) == 1
        assert results[0]["line_number"] == 2
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
