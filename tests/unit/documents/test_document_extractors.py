"""
Unit tests for format-specific document extractors.
"""

import pytest
import os
import tempfile
import json
from jarvis.documents.extractor import (
    PlainTextExtractor,
    MarkdownExtractor,
    JSONYAMLExtractor,
    CSVExtractor,
    HTMLExtractor,
    PDFExtractor,
    DOCXExtractor,
)
from jarvis.documents.errors import OCRRequiredError


def test_markdown_extractor():
    ext = MarkdownExtractor()
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as tmp:
        tmp.write("# Header 1\nParagraph text here.\n\n## Header 2\nAnother section.")
        tmp_path = tmp.name

    try:
        text = ext.extract_text(tmp_path)
        assert "Header 1" in text

        struct = ext.extract_structure(tmp_path)
        assert len(struct.headings) == 2
        assert struct.headings[0]["text"] == "Header 1"
        assert len(struct.sections) == 2
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_json_yaml_extractor():
    ext = JSONYAMLExtractor()
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tmp:
        tmp.write(json.dumps({"database": {"host": "localhost", "port": 5432}}))
        tmp_path = tmp.name

    try:
        val = ext.query_key(tmp_path, "database.host")
        assert val == "localhost"
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_csv_extractor():
    ext = CSVExtractor()
    with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False) as tmp:
        tmp.write("Name,Age,Role\nAlice,30,Developer\nBob,35,Manager\n")
        tmp_path = tmp.name

    try:
        meta = ext.read_metadata(tmp_path)
        assert meta["column_count"] == 3
        assert meta["row_count"] == 2
        assert meta["headers"] == ["Name", "Age", "Role"]
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_html_extractor():
    ext = HTMLExtractor()
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as tmp:
        tmp.write("<html><body><h1>Title</h1><p>Body text</p><script>alert('bad');</script></body></html>")
        tmp_path = tmp.name

    try:
        text = ext.extract_text(tmp_path)
        assert "Body text" in text
        assert "alert" not in text
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_pdf_extractor_ocr_required_error():
    ext = PDFExtractor()
    with tempfile.NamedTemporaryFile("wb", suffix=".pdf", delete=False) as tmp:
        tmp.write(b"%PDF-1.4 empty pdf without text Tj streams")
        tmp_path = tmp.name

    try:
        with pytest.raises(OCRRequiredError):
            ext.extract_text(tmp_path)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
