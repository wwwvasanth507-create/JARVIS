"""
Unit tests for document tools.
"""

import pytest
import os
import tempfile
from jarvis.tools.document_tools import (
    DocumentInspectTool,
    DocumentReadTool,
    DocumentExtractTextTool,
    DocumentSearchTool,
    DocumentSummarizeTool,
    DocumentAskTool,
    DocumentCompareTool,
    DocumentExtractTableTool,
    DocumentCreateTool,
    DocumentConvertTool,
    DOCUMENT_TOOLS
)
from jarvis.security.permissions import PermissionCategory, RiskLevel


def test_document_tools_count():
    assert len(DOCUMENT_TOOLS) == 10


def test_document_read_tool():
    tool = DocumentReadTool()
    assert tool.metadata.name == "document.read"
    assert tool.metadata.permission_requirement == PermissionCategory.READ_FILES
    assert tool.metadata.risk_level == RiskLevel.LOW

    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as tmp:
        tmp.write("Document text content")
        tmp_path = tmp.name

    try:
        res = tool.execute(path=tmp_path)
        assert res.success is True
        assert res.data["text"] == "Document text content"
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_document_create_tool():
    tool = DocumentCreateTool()
    assert tool.metadata.name == "document.create"
    assert tool.metadata.permission_requirement == PermissionCategory.WRITE_FILES
    assert tool.metadata.risk_level == RiskLevel.MEDIUM


    target = os.path.join(tempfile.gettempdir(), "tool_created.md")
    if os.path.exists(target):
        os.remove(target)

    try:
        res = tool.execute(path=target, content="# Created via Tool", format="md")
        assert res.success is True
        assert res.data["created"] is True
    finally:
        if os.path.exists(target):
            os.remove(target)
