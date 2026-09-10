"""
Unit tests for StructuredToolParser.
"""

import pytest
from jarvis.brain.tool_parser import StructuredToolParser


def test_structured_tool_parser_valid_json():
    text = '{"tool": "filesystem.search", "arguments": {"query": "report.pdf"}}'
    tool_name, args, err = StructuredToolParser.parse_tool_call(text)

    assert err is None
    assert tool_name == "filesystem.search"
    assert args == {"query": "report.pdf"}


def test_structured_tool_parser_markdown_code_block():
    text = """Here is the tool call:
```json
{
  "tool": "document.read",
  "arguments": {
    "path": "data/sample.md"
  }
}
```
"""
    tool_name, args, err = StructuredToolParser.parse_tool_call(text)

    assert err is None
    assert tool_name == "document.read"
    assert args == {"path": "data/sample.md"}


def test_structured_tool_parser_invalid_json():
    text = "Not a json payload"
    tool_name, args, err = StructuredToolParser.parse_tool_call(text)

    assert tool_name is None
    assert err is not None
    assert "syntax error" in err.lower() or "empty" in err.lower()
