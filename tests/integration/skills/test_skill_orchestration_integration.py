"""
Integration tests for SkillManager and JarvisOrchestrator.
"""

from jarvis.core.orchestration.orchestrator import JarvisOrchestrator
from jarvis.core.orchestration.state import ExecutionStatus
from jarvis.skills.manager import SkillManager


def test_orchestrator_skill_resolution_application_list():
    skill_mgr = SkillManager()
    orchestrator = JarvisOrchestrator(skill_mgr=skill_mgr)

    # Request matching builtin open_application or list applications
    state = orchestrator.handle("list installed applications")
    assert state.status == ExecutionStatus.COMPLETED
    assert len(state.completed_steps) >= 1


def test_orchestrator_disable_and_enable_skill():
    skill_mgr = SkillManager()

    # Disable system_status skill
    skill_mgr.disable_skill("system_status")
    s = skill_mgr.get_skill("system_status")
    assert s.enabled_at is None or s.state.value == "DISABLED"

    # Re-enable system_status skill
    s_enabled = skill_mgr.enable_skill("system_status")
    assert s_enabled.state.value == "ENABLED"
