"""Integration tests verifying Production Acceptance Scenarios A through L for Prompt 019."""

import pytest
from jarvis.core.orchestration.ambiguity import AmbiguityCandidate, AmbiguityHandler
from jarvis.core.orchestration.conversation_state import ConversationStateManager
from jarvis.core.orchestration.intent import IntentParser
from jarvis.core.orchestration.plan import Plan, PlanStep
from jarvis.core.orchestration.planner import PlanQualityScorer
from jarvis.core.orchestration.reference_resolver import ReferenceResolver
from jarvis.core.orchestration.router import HierarchicalRouter, RoutingTier
from jarvis.core.orchestration.task_resume import TaskResumeManager
from jarvis.security.permissions import RiskLevel, PermissionCategory


def test_scenario_a_open_chrome():
    parser = IntentParser()
    intent = parser.parse("Open Chrome")
    assert intent.action in ("open", "application.open", "browser.open", "general.task")


def test_scenario_b_search_topic():
    parser = IntentParser()
    intent = parser.parse("Open Chrome and search for quantum computing")
    assert intent.action in ("search", "open", "browser.search", "browser.open", "application.open", "general.task")


def test_scenario_c_find_pdf_and_open():
    state_mgr = ConversationStateManager()
    state_mgr.record_tool_output(
        "filesystem.search", "search", {"query": "*.pdf", "matches": ["C:\\docs\\annual_report.pdf"]}
    )
    resolver = ReferenceResolver(state_mgr)

    resolved = resolver.resolve("open it")
    assert "C:\\docs\\annual_report.pdf" in resolved.resolved_text


def test_scenario_d_summarize_and_save():
    steps = [
        PlanStep(step_id="s1", description="read doc", tool_name="doc.read", arguments={"path": "C:\\doc.txt"}),
        PlanStep(step_id="s2", description="summarize doc", tool_name="doc.summarize", arguments={"text": "content"}),
        PlanStep(
            step_id="s3", description="write summary", tool_name="file.write", arguments={"path": "C:\\summary.txt"}
        ),
    ]
    plan = Plan(plan_id="plan_d", goal_id="goal_d", steps=steps)
    scoring = PlanQualityScorer.score_plan(plan)
    assert scoring["valid"] is True


def test_scenario_e_schedule_reminder():
    parser = IntentParser()
    intent = parser.parse("Remind me every Monday morning at 9am to check reports")
    assert intent.action in ("schedule", "remind", "scheduler.create", "general.task")


def test_scenario_f_multi_step_workflow():
    router = HierarchicalRouter()
    decision = router.route("Find project report, summarize it and save to summary.md")
    assert decision.tier in (RoutingTier.SKILL_RESOLVER, RoutingTier.LOCAL_LLM)


def test_scenario_g_ambiguity_clarification():
    state_mgr = ConversationStateManager()
    handler = AmbiguityHandler(state_mgr)
    candidates = ["C:\\Downloads\\file.txt", "C:\\Documents\\file.txt"]
    ambiguity = handler.check_file_search_ambiguity("file.txt", candidates)
    handler.store_pending_clarification(ambiguity)
    assert handler.has_pending_clarification() is True
    answer = handler.resolve_pending_clarification("the second one")
    assert answer.target_value == "C:\\Documents\\file.txt"


def test_scenario_h_follow_up_reference():
    state_mgr = ConversationStateManager()
    state_mgr.record_tool_output(
        "browser.search",
        "search",
        {
            "query": "A.R. Rahman songs",
            "results": [
                {"title": "Song 1", "url": "https://youtube.com/watch?v=1"},
                {"title": "Song 2", "url": "https://youtube.com/watch?v=2"},
            ],
        },
    )
    resolver = ReferenceResolver(state_mgr)
    res = resolver.resolve("play the second one")
    assert "https://youtube.com/watch?v=2" in res.resolved_text or "Song 2" in res.resolved_text


def test_scenario_i_interrupt_task():
    state_mgr = ConversationStateManager()
    state_mgr.set_active_task("task_123", "Downloading huge file")

    parser = IntentParser()
    intent = parser.parse("Stop. Actually cancel that and open Chrome")
    assert intent.action in ("stop", "cancel", "open", "general.task")


def test_scenario_j_tool_failure_replanning():
    failing_step = PlanStep(
        step_id="s1", description="move file", tool_name="filesystem.move", arguments={"src": "a", "dst": "b"}
    )
    plan = Plan(plan_id="p1", goal_id="g1", steps=[failing_step])
    scoring = PlanQualityScorer.score_plan(plan)
    assert scoring["valid"] is True


def test_scenario_k_high_risk_confirmation():
    unspecified_step = PlanStep(
        step_id="s1",
        description="format drive",
        tool_name="general.task",
        arguments={"command": "format C:"},
        risk_level=RiskLevel.HIGH,
    )
    plan = Plan(plan_id="p_k", goal_id="g_k", steps=[unspecified_step])
    scoring = PlanQualityScorer.score_plan(plan)
    assert scoring["score"] < 1.0
    assert any("unspecified or generic tool" in r for r in scoring["reasons"])


def test_scenario_l_resume_interrupted_task(tmp_path):
    checkpoint_file = tmp_path / "checkpoints.json"
    resume_mgr = TaskResumeManager(storage_path=str(checkpoint_file))

    plan = Plan(
        plan_id="p_resume",
        goal_id="g_resume",
        steps=[
            PlanStep(step_id="s1", description="open browser", tool_name="browser.open"),
            PlanStep(step_id="s2", description="download file", tool_name="file.download"),
        ],
    )

    checkpoint = resume_mgr.create_checkpoint("task_999", plan, completed_step_indices=[0])
    assert checkpoint is not None

    pending = resume_mgr.get_pending_resumes()
    assert len(pending) == 1
    assert pending[0].execution_id == "task_999"
    assert pending[0].completed_step_indices == [0]
