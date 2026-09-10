"""
Unit tests for DocumentNormalizer and DocumentChunker.
"""

import pytest
from jarvis.documents.normalizer import DocumentNormalizer
from jarvis.documents.chunker import DocumentChunker
from jarvis.documents.models import DocumentStructure
from jarvis.documents.errors import DocumentLimitExceededError


def test_document_normalizer():
    norm = DocumentNormalizer()
    raw = "Line 1\r\nLine 2   \r\n\n\n\nLine 3"
    cleaned = norm.normalize(raw)
    assert cleaned == "Line 1\nLine 2\n\nLine 3"


def test_document_chunker_bounded_size():
    chunker = DocumentChunker(chunk_size=100, chunk_overlap=10)
    text = "Word " * 100 # 500 characters
    chunks = chunker.chunk_text(text, "doc_test")

    assert len(chunks) > 1
    for chk in chunks:
        assert len(chk.content) <= 120
        assert chk.document_id == "doc_test"


def test_document_chunker_max_chunks_exceeded():
    chunker = DocumentChunker(chunk_size=10, max_chunks=2)
    text = "A" * 100
    with pytest.raises(DocumentLimitExceededError):
        chunker.chunk_text(text, "doc_test")
