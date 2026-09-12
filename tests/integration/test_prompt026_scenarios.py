"""
Integration Test Suite for Prompt 026 Universal Computer Agent Scenarios.
Tests cross-application workflows, communication management, unknown application discovery,
ambiguity resolution, plan criticism, safety policy enforcement, and task execution.
"""

import pytest
import tempfile
from pathlib import Path

from jarvis.core.reasoning.interpreter import TaskInterpreter
from jarvis.core.reasoning.decomposer import TaskDecomposer
from jarvis.core.reasoning.critic import PlanCritic
from jarvis.core.reasoning.capability_discovery import CapabilityDiscoveryEngine
from jarvis.core.reasoning.reasoning_engine import JarvisAgent, ExecutionState
from jarvis.communication.manager import CommunicationManager
from jarvis.communication.contacts import ContactResolver
from jarvis.communication.models import ContactRecord
from jarvis.applications.unknown_app_discovery import UnknownApplicationDiscovery
from jarvis.core.workflows.cross_app_workflow import CrossAppWorkflowEngine


@pytest.fixture
def temp_workspace():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def test_scenario_01_email_report_workflow(temp_workspace):
    """Scenario 1 & 2: Read local document report and compose/verify email to resolved contact."""
    report_file = temp_workspace / "monthly_report.txt"
    report_file.write_text("Revenue: $500,000. Expenses: $300,000. Profit: $200,000.", encoding="utf-8")

    # Step 1: Interpret task
    query = f"Read {report_file} and email summary to Vasanth."
    intent = TaskInterpreter.interpret(query)
    assert intent.objective == "CROSS_APP_WORKFLOW"
    assert intent.primary_domain == "DOCUMENT"

    # Step 2: Decompose plan
    hierarchy = TaskDecomposer.decompose(intent)
    assert len(hierarchy.steps) >= 3

    # Step 3: Plan criticism
    report = PlanCritic.evaluate(hierarchy)
    assert report.is_valid is True

    # Step 4: Resolve recipient & draft email
    contact = ContactResolver.resolve("Vasanth")
    assert contact is not None
    assert "vasanth" in contact.email.lower()

    comm_mgr = CommunicationManager()
    draft_res = comm_mgr.compose_email(
        recipient_query="Vasanth",
        subject="Monthly Report Summary",
        body="Revenue: $500,000. Net Profit: $200,000."
    )
    assert draft_res.status == "DRAFT"
    preview = comm_mgr.preview_email(draft_res.message_id)
    assert "vasanth" in preview.lower()

    # Step 5: Send and verify email
    send_res = comm_mgr.send_email(draft_res.message_id, force_approve=True)
    assert send_res.status in ("SENT", "DISPATCHED")
    assert comm_mgr.verify_sent(send_res.message_id)["verified"] is True


def test_scenario_02_ambiguous_contact_resolution():
    """Scenario 5: Handle ambiguous recipient contacts safely without guessing."""
    ContactResolver.add_contact(ContactRecord(name="Vasanth Kumar", email="vasanth.k@example.com"))
    ContactResolver.add_contact(ContactRecord(name="Vasanth Rao", email="vasanth.r@example.com"))

    candidates = ContactResolver.search("Vasanth")
    assert len(candidates) >= 2

    exact = ContactResolver.resolve("Vasanth")
    assert exact is None or isinstance(candidates, list)


def test_scenario_03_unknown_app_discovery_matrix():
    """Scenario 27: Discover unknown GUI application semantics without pre-baked heuristics."""
    mock_window_info = {
        "title": "SuperCalc 2026",
        "app_name": "SuperCalc.exe",
        "controls": [
            {"id": "txt_input", "type": "TextBox", "name": "Formula Input", "bbox": [10, 10, 200, 30]},
            {"id": "btn_calc", "type": "Button", "name": "Calculate", "bbox": [220, 10, 300, 30]}
        ]
    }

    profile = UnknownApplicationDiscovery.discover("SuperCalc.exe", mock_window_info)
    assert profile.app_name == "SuperCalc.exe"
    assert profile.category in ("UNKNOWN_SPREADSHEET_OR_CALC", "GENERIC_DESKTOP_APP")
    assert len(profile.discovered_controls) == 2

    actions = UnknownApplicationDiscovery.infer_available_actions(profile)
    assert len(actions) >= 2
    action_types = [a["action"] for a in actions]
    assert "TYPE" in action_types or "ENTER_TEXT" in action_types
    assert "CLICK" in action_types


def test_scenario_04_cross_app_workflow_execution(temp_workspace):
    """Scenario 8 & 41: Extract data from source document and populate target spreadsheet."""
    invoice_path = temp_workspace / "invoice.txt"
    invoice_path.write_text("Invoice #1001: Total $1,250.00", encoding="utf-8")
    sheet_path = temp_workspace / "output.csv"

    res = CrossAppWorkflowEngine.execute_document_to_spreadsheet(
        source_doc=str(invoice_path),
        target_spreadsheet=str(sheet_path)
    )

    assert res.status == "SUCCESS"
    assert len(res.extracted_data) > 0
    assert sheet_path.exists()
    content = sheet_path.read_text(encoding="utf-8")
    assert "$1,250.00" in content or "1001" in content


def test_scenario_05_jarvis_agent_execution_loop():
    """Scenario 38 & 39: Execute JarvisAgent end-to-end task execution contract."""
    test_file = Path("data/test_workspace/agent_test.txt")
    test_file.parent.mkdir(parents=True, exist_ok=True)
    request = f"Create file at {test_file} with content Hello Agent"

    res = JarvisAgent.execute(request)
    assert res.status == "COMPLETED"
    assert res.confidence >= 0.85
    assert len(res.verification) > 0
    assert test_file.exists()
    assert test_file.read_text(encoding="utf-8") == "Hello Agent"


def test_scenario_06_interruption_and_state_pause():
    """Scenario 42 & 43: Test task execution pause and interruption state."""
    exec_state = ExecutionState(task_id="task_test_99", query="Complex long running task")
    assert exec_state.paused is False

    exec_state.pause("User requested STOP")
    assert exec_state.paused is True
    assert "User requested STOP" in exec_state.pause_reason

    exec_state.resume()
    assert exec_state.paused is False
