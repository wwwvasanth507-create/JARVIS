"""
End-to-End Acceptance Test Suite for Prompt 026 Universal Computer Agent.
Verifies the full natural language -> reasoning -> plan critic -> execution -> verification -> supervisory update pipeline.
"""

import pytest
from pathlib import Path

from jarvis.core.reasoning.reasoning_engine import JarvisAgent
from jarvis.ui.live_monitor import LiveTaskMonitorWidget


@pytest.fixture
def workspace_env():
    p = Path("data/test_workspace")
    p.mkdir(parents=True, exist_ok=True)
    doc = p / "contract.txt"
    doc.write_text("Contract Value: $45,000. Client: Acme Corp.", encoding="utf-8")
    out = p / "summary_mail.txt"
    yield {"dir": p, "doc": doc, "out": out}


def test_e2e_universal_agent_filesystem_task(workspace_env):
    """E2E Test: Filesystem task execution from natural language within allowed workspace."""
    target_file = workspace_env["dir"] / "e2e_output.txt"
    query = f"Create file at {target_file} with content EndToEnd Test Success"

    result = JarvisAgent.execute(query)
    assert result.status == "COMPLETED"
    assert result.confidence >= 0.85
    assert target_file.exists()
    assert target_file.read_text(encoding="utf-8") == "EndToEnd Test Success"


def test_e2e_universal_agent_email_task():
    """E2E Test: Email intent resolution, preview, approval gate, send, and verification."""
    query = "Send email to Vasanth saying meeting is postponed to 4 PM."

    result = JarvisAgent.execute(query)
    assert result.status in ("COMPLETED", "AWAITING_APPROVAL", "REQUIRES_CONFIRMATION")
    assert len(result.steps) > 0


def test_e2e_universal_agent_cross_app_workflow(workspace_env):
    """E2E Test: Extract document info and transition across applications."""
    doc_path = workspace_env["doc"]
    query = f"Read {doc_path} and email summary to Vasanth."

    result = JarvisAgent.execute(query)
    assert result.status in ("COMPLETED", "AWAITING_APPROVAL", "REQUIRES_CONFIRMATION")
    assert len(result.steps) >= 3


def test_e2e_universal_agent_live_supervision_widget():
    """E2E Test: Verify LiveTaskMonitorWidget updates live task state during execution."""
    widget = LiveTaskMonitorWidget()

    widget.update_task_state({
        "task": "E2E Live Task",
        "goal": "SEND_EMAIL",
        "subtask": "Selecting recipient field",
        "app": "Browser -> Webmail",
        "action": "CLICK",
        "target": "To: input field",
        "confidence": 0.98,
        "next_action": "Type vasanth@example.com",
        "status": "EXECUTING"
    })

    summary = widget.get_current_summary()
    assert summary["task"] == "E2E Live Task"
    assert summary["status"] == "EXECUTING"
    assert summary["confidence"] == 0.98
    assert summary["app"] == "Browser -> Webmail"
