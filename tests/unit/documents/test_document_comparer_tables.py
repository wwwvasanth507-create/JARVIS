"""
Unit tests for DocumentComparer and TableExtractor.
"""

import pytest
import os
import tempfile
from jarvis.documents.manager import DocumentManager
from jarvis.documents.tables import TableExtractor


def test_document_comparison():
    mgr = DocumentManager()
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as tmp1:
        tmp1.write("# Section A\nOriginal content")
        tmp1_path = tmp1.name

    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as tmp2:
        tmp2.write("# Section A\nModified content\n\n# Section B\nNew section")
        tmp2_path = tmp2.name

    try:
        comp = mgr.compare_documents(tmp1_path, tmp2_path)
        assert "Section B" in comp.added_sections
        assert comp.document_a_id != comp.document_b_id
    finally:
        for p in [tmp1_path, tmp2_path]:
            if os.path.exists(p):
                os.remove(p)


def test_table_extraction_and_conversion():
    extractor = TableExtractor()
    with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False) as tmp:
        tmp.write("Header1,Header2\nValue1,Value2\nValue3,Value4\n")
        tmp_path = tmp.name

    try:
        tables = extractor.extract_tables(tmp_path, ".csv")
        assert len(tables) == 1
        tbl = tables[0]
        assert tbl.headers == ["Header1", "Header2"]
        assert len(tbl.rows) == 2

        json_fmt = extractor.convert_table(tbl, "json")
        assert '"Header1": "Value1"' in json_fmt

        md_fmt = extractor.convert_table(tbl, "md")
        assert "| Header1 | Header2 |" in md_fmt
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
