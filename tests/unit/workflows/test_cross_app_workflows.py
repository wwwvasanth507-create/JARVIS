"""
Unit tests for JARVIS Cross-Application Workflow Engine.
"""

import pytest
from jarvis.core.workflows.cross_app_workflow import CrossAppWorkflowEngine, CrossAppWorkflowResult
from jarvis.tools.filesystem_tools import WriteFileTool


def test_01_cross_app_doc_to_email_workflow(tmp_path):
    # Setup test workspace report file
    test_dir = tmp_path / "data" / "test_workspace"
    test_dir.mkdir(parents=True, exist_ok=True)
    report_file = test_dir / "monthly_report.txt"
    
    report_file.write_text(
        "Monthly Report: All quarterly targets exceeded by 15%. Operations normal.",
        encoding="utf-8"
    )

    wf_engine = CrossAppWorkflowEngine.get_instance()
    res = wf_engine.execute_doc_to_email_workflow(
        doc_search_query=str(report_file),
        recipient_query="Vasanth",
        email_subject="Monthly Report Summary",
        search_root=str(test_dir),
        force_approve=True
    )

    assert isinstance(res, CrossAppWorkflowResult)
    assert res.status == "COMPLETED"
    assert len(res.steps_executed) == 5
    assert res.steps_executed[0].success is True
    assert res.steps_executed[-1].verified is True
