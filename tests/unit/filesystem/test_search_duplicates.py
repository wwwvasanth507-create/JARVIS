"""
Unit tests for file search and staged duplicate detection.
"""

import pytest
from pathlib import Path
from jarvis.filesystem.search import FileSearchEngine, SearchQuery
from jarvis.filesystem.duplicates import DuplicateFinder


def test_file_search(tmp_path):
    (tmp_path / "doc1.pdf").write_text("PDF content 1")
    (tmp_path / "doc2.pdf").write_text("PDF content 2")
    (tmp_path / "notes.txt").write_text("Text content")

    engine = FileSearchEngine()
    query = SearchQuery(root_path=str(tmp_path), extension=".pdf")
    res = engine.search(query)

    assert res.total_found == 2
    assert len(res.results) == 2
    names = {r.name for r in res.results}
    assert names == {"doc1.pdf", "doc2.pdf"}


def test_find_duplicates(tmp_path):
    content = "A" * 2048  # 2KB sample content
    file_a = tmp_path / "photo1.jpg"
    file_b = tmp_path / "photo2.jpg"
    file_c = tmp_path / "unique.jpg"

    file_a.write_text(content)
    file_b.write_text(content)
    file_c.write_text("B" * 2048)

    finder = DuplicateFinder()
    report = finder.find_duplicates(tmp_path, min_file_size=100)

    assert report.duplicate_groups_found == 1
    assert len(report.groups) == 1
    assert report.groups[0].count == 2
    assert set(report.groups[0].files) == {
        str(file_a.resolve(strict=False)),
        str(file_b.resolve(strict=False)),
    }
