"""
Unit tests for targeted file editing, backup creation, and JSON editing.
"""

import json
import pytest
from pathlib import Path
from jarvis.filesystem.editor import FileEditor
from jarvis.filesystem.errors import VerificationFailed


def test_replace_exact_text_edit(tmp_path):
    target = tmp_path / "config.txt"
    target.write_text("endpoint=http://old-api.internal\nport=8080", encoding="utf-8")

    editor = FileEditor()
    res = editor.edit_file(
        target,
        operation="replace_exact",
        target_text="http://old-api.internal",
        replacement_text="http://new-api.internal",
        create_backup_file=True,
    )

    assert res.verified
    assert res.backup_path is not None
    assert Path(res.backup_path).exists()
    assert "http://new-api.internal" in target.read_text()


def test_edit_json_key(tmp_path):
    target = tmp_path / "settings.json"
    data = {"mode": "debug", "version": 1}
    target.write_text(json.dumps(data), encoding="utf-8")

    editor = FileEditor()
    res = editor.edit_file(
        target,
        operation="edit_json_key",
        json_key="mode",
        json_value="production",
        create_backup_file=False,
    )

    assert res.verified
    updated = json.loads(target.read_text())
    assert updated["mode"] == "production"
