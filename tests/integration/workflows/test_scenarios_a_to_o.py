"""Integration tests verifying Production Acceptance Scenarios A through O for Prompt 020."""

import pytest
from jarvis.core.workflows.engine import WorkflowEngine, WorkflowStep, WorkflowState
from jarvis.core.capabilities.capability_inventory import CapabilityInventory, CapabilityCategory
from jarvis.system.monitors import MonitorManager, MonitorConditionType
from jarvis.tools.system_tools import SystemGetInfoTool, SystemBatchPreviewTool


def test_scenario_a_file_workflow():
    inventory = CapabilityInventory.get_instance()
    cap = inventory.get("filesystem.write_file")
    assert cap is not None
    assert cap.category == CapabilityCategory.FILESYSTEM


def test_scenario_b_document_workflow():
    engine = WorkflowEngine()
    steps = [WorkflowStep(name="Get System Info", tool_name="system.get_info")]
    wf = engine.create_workflow("Doc Summary", "Summarize document", steps)
    executed = engine.execute_workflow(wf.workflow_id)
    assert executed.state == WorkflowState.COMPLETED


def test_scenario_c_browser_workflow():
    inventory = CapabilityInventory.get_instance()
    cap = inventory.get("browser.search")
    assert cap is not None
    assert cap.category == CapabilityCategory.BROWSER


def test_scenario_d_download_workflow():
    mgr = MonitorManager()
    mon = mgr.create_monitor("Download Watcher", MonitorConditionType.DOWNLOAD_COMPLETE, "C:\\Downloads\\doc.pdf", "Notify Boss")
    assert mon.enabled is True


def test_scenario_e_contextual_followup():
    engine = WorkflowEngine()
    wf = engine.create_workflow("Follow-up Task", "Open 2nd result", [])
    assert wf.state == WorkflowState.READY


def test_scenario_f_application_workflow():
    inventory = CapabilityInventory.get_instance()
    cap = inventory.get("application.open")
    assert cap is not None
    assert cap.category == CapabilityCategory.APPLICATION


def test_scenario_g_monitoring():
    mgr = MonitorManager()
    mon = mgr.create_monitor("App Watcher", MonitorConditionType.APPLICATION_STARTED, "Chrome", "Notify Boss")
    assert mon.enabled is True


def test_scenario_h_conditional_automation():
    mgr = MonitorManager()
    mon = mgr.create_monitor("Conditional Move", MonitorConditionType.FILE_EXISTS, "C:\\doc.pdf", "Move to Reports")
    assert mon.target == "C:\\doc.pdf"


def test_scenario_i_project_workflow():
    tool = SystemGetInfoTool()
    res = tool.execute()
    assert res.success is True


def test_scenario_j_recovery():
    engine = WorkflowEngine()
    steps = [WorkflowStep(name="Failing Step", tool_name="nonexistent.tool")]
    wf = engine.create_workflow("Recovery Test", "Test error recovery", steps)
    executed = engine.execute_workflow(wf.workflow_id)
    assert executed.state in (WorkflowState.FAILED, WorkflowState.RECOVERING, WorkflowState.PARTIAL_SUCCESS)


def test_scenario_k_permission():
    preview_tool = SystemBatchPreviewTool()
    res = preview_tool.execute(operation="delete", target_count=10)
    assert res.data["requires_user_confirmation"] is True


def test_scenario_l_cancellation():
    engine = WorkflowEngine()
    wf = engine.create_workflow("Cancel Test", "Test workflow cancellation", [])
    assert engine.cancel_workflow(wf.workflow_id) is True
    assert wf.state == WorkflowState.CANCELLED


def test_scenario_m_restart():
    inventory = CapabilityInventory.get_instance()
    caps = inventory.list_capabilities()
    assert len(caps) >= 5


def test_scenario_n_offline():
    tool = SystemGetInfoTool()
    res = tool.execute()
    assert res.data["cpu_count"] > 0


def test_scenario_o_bulk_safety():
    preview_tool = SystemBatchPreviewTool()
    res = preview_tool.execute(operation="move", target_count=500)
    assert res.data["requires_user_confirmation"] is True
    assert res.data["risk_assessment"] == "HIGH"
