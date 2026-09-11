"""
Unit tests for Form, Table, and Dialog models and managers.
"""

import pytest
from jarvis.computer.vision.forms import Form, FormField
from jarvis.computer.vision.tables import Table, TableRow, TableCell
from jarvis.computer.vision.dialogs import DialogManager, DialogType, DialogSeverity


def test_table_row_and_cell_queries():
    c1 = TableCell(row_index=0, col_index=0, column_name="Name", value="John Doe")
    c2 = TableCell(row_index=0, col_index=1, column_name="Status", value="Active")
    row = TableRow(row_index=0, cells={"name": c1, "status": c2})
    tbl = Table(table_id="t1", columns=["Name", "Status"], rows=[row])

    matched_row = tbl.find_row_by_column_value("Name", "John")
    assert matched_row is not None
    assert tbl.get_cell_value(0, "Status") == "Active"


def test_form_field_preview_and_redaction():
    f1 = FormField(field_id="1", label="Username", current_value="")
    f2 = FormField(field_id="2", label="Password", control_type="password", current_value="")
    form = Form(form_id="f1", fields=[f1, f2])

    preview = form.generate_preview({"Username": "alice", "Password": "Secret123!"})
    assert preview.fields_to_populate["Password"] == "********"
    assert "Password" in preview.sensitive_fields_detected


def test_security_dialog_protection():
    dlg = DialogManager.classify_dialog(title="Grant Permission", message="Allow app to modify system files", buttons=["Allow", "Deny"])
    assert dlg.is_security_prompt is True
    assert DialogManager.can_auto_dismiss(dlg) is False
