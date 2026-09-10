"""
Unit tests for safe reading, encoding detection, atomic writing, and overwrite guards.
"""

import pytest
from pathlib import Path
from jarvis.filesystem.reader import FileReader
from jarvis.filesystem.writer import FileWriter
from jarvis.filesystem.errors import FileExists, UnsupportedFileType


def test_atomic_file_writer_and_reader(tmp_path):
    target = tmp_path / "test_doc.txt"
    content = "Line 1: Hello JARVIS\nLine 2: CPU First Architecture\nLine 3: Prompt 007"

    # Write file
    w_res = FileWriter.write_file(target, content, overwrite=False, atomic=True)
    assert w_res.verified
    assert w_res.bytes_written == len(content.encode("utf-8"))
    assert target.exists()

    # Read file
    reader = FileReader()
    r_res = reader.read_text_file(target)
    assert r_res.content == content
    assert r_res.total_lines == 3
    assert not r_res.truncated


def test_overwrite_protection(tmp_path):
    target = tmp_path / "existing.txt"
    FileWriter.write_file(target, "Original Content", overwrite=False)

    with pytest.raises(FileExists):
        FileWriter.write_file(target, "New Content", overwrite=False)

    # With overwrite=True
    w_res = FileWriter.write_file(target, "New Content", overwrite=True)
    assert w_res.overwritten
    assert target.read_text() == "New Content"


def test_reader_line_range(tmp_path):
    target = tmp_path / "lines.txt"
    lines = [f"Line {i}" for i in range(1, 11)]
    target.write_text("\n".join(lines), encoding="utf-8")

    reader = FileReader()
    r_res = reader.read_text_file(target, start_line=3, end_line=5)
    assert r_res.content == "Line 3\nLine 4\nLine 5"
    assert r_res.truncated
