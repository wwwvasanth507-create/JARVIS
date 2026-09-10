"""
Unit tests for DocumentCreator, DocumentConverter, and DocumentVerificationManager.
"""

import pytest
import os
import tempfile
from jarvis.documents.manager import DocumentManager
from jarvis.documents.errors import DocumentCreationError


def test_document_creation_atomic():
    mgr = DocumentManager()
    target = os.path.join(tempfile.gettempdir(), "test_created_doc.md")
    if os.path.exists(target):
        os.remove(target)

    try:
        res = mgr.create_document(target, "# Title\nCreated content", format_type="md", overwrite=False)
        assert res["created"] is True
        assert res["verified"] is True
        assert os.path.exists(target)
    finally:
        if os.path.exists(target):
            os.remove(target)


def test_document_creation_overwrite_protection():
    mgr = DocumentManager()
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as tmp:
        tmp.write("Existing file")
        tmp_path = tmp.name

    try:
        with pytest.raises(DocumentCreationError):
            mgr.create_document(tmp_path, "New content", overwrite=False)

        # Overwrite=True should succeed
        res = mgr.create_document(tmp_path, "New content", overwrite=True)
        assert res["created"] is True
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_document_conversion():
    mgr = DocumentManager()
    src_csv = os.path.join(tempfile.gettempdir(), "source.csv")
    tgt_json = os.path.join(tempfile.gettempdir(), "target.json")

    with open(src_csv, "w", encoding="utf-8") as f:
        f.write("col1,col2\nval1,val2\n")

    try:
        res = mgr.convert_document(src_csv, tgt_json, overwrite=True)
        assert res["converted"] is True
        assert res["verified"] is True
        assert os.path.exists(tgt_json)
        with open(tgt_json, "r", encoding="utf-8") as f:
            assert "col1" in f.read()
    finally:
        for p in [src_csv, tgt_json]:
            if os.path.exists(p):
                os.remove(p)
