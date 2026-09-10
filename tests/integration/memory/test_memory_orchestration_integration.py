"""
Integration tests for MemoryManager and JarvisOrchestrator.
"""

from jarvis.core.orchestration.orchestrator import JarvisOrchestrator
from jarvis.core.orchestration.state import ExecutionStatus
from jarvis.memory.manager import MemoryManager


def test_orchestrator_explicit_memory_statement():
    mem_mgr = MemoryManager(db_path=":memory:")
    orchestrator = JarvisOrchestrator(memory_mgr=mem_mgr)

    # 1. Statement: "Remember that my project folder is D:\Projects\JARVIS"
    state = orchestrator.handle("Remember that my project folder is D:\\Projects\\JARVIS")
    assert state.status == ExecutionStatus.COMPLETED
    assert len(state.observations) == 1

    # 2. Retrieve project path directly from MemoryManager
    proj = mem_mgr.get_project("path")
    assert proj is not None
    assert proj.path == "D:\\Projects\\JARVIS"


def test_memory_preference_retrieval():
    mem_mgr = MemoryManager(db_path=":memory:")
    mem_mgr.set_preference("preferred_theme", "dark")

    assert mem_mgr.get_preference("preferred_theme") == "dark"
