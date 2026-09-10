"""
Unit tests for DocumentDetector and DocumentMetadataExtractor.
"""

import pytest
import os
import tempfile
from jarvis.documents.detector import DocumentDetector
from jarvis.documents.metadata import DocumentMetadataExtractor
from jarvis.documents.errors import UnsupportedDocumentFormatError, DocumentLimitExceededError


def test_document_detection_supported():
    detector = DocumentDetector()
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as tmp:
        tmp.write("# Test Document\nSample text")
        tmp_path = tmp.name

    try:
        res = detector.detect(tmp_path)
        assert res["extension"] == ".md"
        assert res["classification"] == "text"
        assert res["is_binary"] is False
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_document_detection_unsupported():
    detector = DocumentDetector()
    with tempfile.NamedTemporaryFile("w", suffix=".xyz_unsupported", delete=False) as tmp:
        tmp.write("data")
        tmp_path = tmp.name

    try:
        with pytest.raises(UnsupportedDocumentFormatError):
            detector.detect(tmp_path)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_document_metadata_extraction():
    extractor = DocumentMetadataExtractor(max_file_size_bytes=1024*1024)
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as tmp:
        tmp.write("Hello World File Metadata")
        tmp_path = tmp.name

    try:
        info = extractor.extract_metadata(tmp_path)
        assert info.filename == os.path.basename(tmp_path)
        assert info.extension == ".txt"
        assert info.size > 0
        assert len(info.content_hash) == 64
        assert info.document_id.startswith("doc_")
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_document_metadata_size_limit_exceeded():
    extractor = DocumentMetadataExtractor(max_file_size_bytes=10) # 10 bytes limit
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as tmp:
        tmp.write("This content is longer than 10 bytes limit.")
        tmp_path = tmp.name

    try:
        with pytest.raises(DocumentLimitExceededError):
            extractor.extract_metadata(tmp_path)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
