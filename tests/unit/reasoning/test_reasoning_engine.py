"""
Unit tests for JARVIS Reasoning Engine, Interpreter, Decomposer, PlanCritic, and WorldState.
"""

import pytest
from jarvis.core.reasoning.interpreter import TaskInterpreter, StructuredIntent
from jarvis.core.reasoning.decomposer import TaskDecomposer, TaskHierarchy
from jarvis.core.reasoning.critic import PlanCritic, PlanRepairer
from jarvis.core.reasoning.capability_discovery import CapabilityDiscoveryEngine
from jarvis.core.reasoning.world_state import WorldState
from jarvis.core.reasoning.reasoning_engine import ReasoningEngine, JarvisAgent


def test_01_task_interpreter_communication():
    intent = TaskInterpreter.interpret("Send email to Vasanth saying the meeting is postponed to 4 PM")
    assert intent.objective == "SEND_EMAIL"
    assert intent.primary_domain == "COMMUNICATION"
    assert intent.recipient is not None
    assert "Vasanth" in intent.recipient
    assert intent.content is not None
    assert "postponed" in intent.content
    assert intent.requires_boss_approval is True


def test_02_task_interpreter_filesystem():
    intent = TaskInterpreter.interpret("Create file at data/test_workspace/hello.txt with content Hello Boss")
    assert intent.objective == "FILESYSTEM_OPERATION"
    assert intent.primary_domain == "FILESYSTEM"
    assert intent.target_path == "data/test_workspace/hello.txt"


def test_03_task_decomposer():
    intent = TaskInterpreter.interpret("Send email to Vasanth saying hello")
    hierarchy = TaskDecomposer.decompose(intent)
    assert hierarchy.goal_title is not None
    assert len(hierarchy.steps) >= 4
    step_actions = [s.action_type for s in hierarchy.steps]
    assert "DISCOVER" in step_actions
    assert "COMPOSE" in step_actions
    assert "PREVIEW" in step_actions
    assert "VERIFY" in step_actions


def test_04_plan_critic_and_repairer():
    intent = TaskInterpreter.interpret("Send email to Vasanth saying hello")
    hierarchy = TaskDecomposer.decompose(intent)
    report = PlanCritic.evaluate(hierarchy)
    assert report.is_valid is True

    repaired = PlanRepairer.repair(hierarchy, report)
    assert len(repaired.steps) >= len(hierarchy.steps)


def test_05_capability_discovery():
    engine = CapabilityDiscoveryEngine.get_instance()
    graph = engine.discover_all()
    assert graph.total_nodes > 0
    assert len(graph.tools) > 100

    best_tool = engine.find_best_tool_for_intent("FILESYSTEM", ["write", "create"])
    assert best_tool is not None


def test_06_world_state():
    ws = WorldState.get_instance()
    summary = ws.get_grounded_summary()
    assert "os" in summary
    assert "active_window" in summary


def test_07_jarvis_agent_execution():
    res = JarvisAgent.execute("Create file at data/test_workspace/reasoning_test.txt with content Reasoning Operational")
    assert res.status == "COMPLETED"
    assert res.execution_time_ms > 0.0
    assert len(res.steps) >= 1
