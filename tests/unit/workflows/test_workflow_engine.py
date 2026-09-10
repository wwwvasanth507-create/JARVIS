"""Unit tests for WorkflowEngine and WorkflowTemplateRegistry."""

import pytest
from jarvis.core.workflows.engine import WorkflowEngine, WorkflowStep, WorkflowState
from jarvis.core.workflows.templates import WorkflowTemplateRegistry


def test_workflow_creation_and_execution():
    engine = WorkflowEngine()

    steps = [
        WorkflowStep(name="Get System Info", tool_name="system.get_info", arguments={}),
        WorkflowStep(name="Check Cleanup", tool_name="system.check_cleanup", arguments={}),
    ]
    wf = engine.create_workflow(name="System Diagnostics Workflow", goal="Check system status", steps=steps)

    assert wf.state == WorkflowState.READY
    executed_wf = engine.execute_workflow(wf.workflow_id)

    assert executed_wf.state == WorkflowState.COMPLETED
    assert executed_wf.progress_percentage == 100.0


def test_workflow_pause_and_resume():
    engine = WorkflowEngine()
    steps = [WorkflowStep(name="Step 1", tool_name="system.get_info")]
    wf = engine.create_workflow("Pause Test", "Test pause", steps)

    wf.update_state(WorkflowState.RUNNING)
    assert engine.pause_workflow(wf.workflow_id, reason="Testing pause") is True
    assert wf.state == WorkflowState.PAUSED

    assert engine.resume_workflow(wf.workflow_id) is True
    assert wf.state == WorkflowState.RUNNING


def test_workflow_template_registry():
    wf = WorkflowTemplateRegistry.get_template("research_and_save", {"query": "AI Agents", "out_file": "C:\\temp\\ai.md"})
    assert wf.name == "Research & Save"
    assert len(wf.steps) == 3
    assert wf.steps[0].tool_name == "browser.search"
