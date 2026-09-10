"""
Unit tests for safe file organization plan generation and execution.
"""

import pytest
from pathlib import Path
from jarvis.filesystem.organization import FileOrganizer


def test_file_organization_plan_and_execution(tmp_path):
    downloads = tmp_path / "Downloads"
    downloads.mkdir()

    (downloads / "doc.pdf").write_text("PDF content")
    (downloads / "image.png").write_text("PNG content")
    (downloads / "archive.zip").write_text("ZIP content")

    organizer = FileOrganizer()
    plan = organizer.generate_plan(downloads)

    assert plan.total_files_to_move == 3
    assert "PDF" in plan.category_counts
    assert "Image" in plan.category_counts
    assert "Archive" in plan.category_counts

    # Execute plan
    report = organizer.execute_plan(plan)
    assert report.successful_moves == 3
    assert report.failed_moves == 0

    assert (downloads / "Documents" / "PDFs" / "doc.pdf").exists()
    assert (downloads / "Pictures" / "image.png").exists()
    assert (downloads / "Archives" / "archive.zip").exists()
