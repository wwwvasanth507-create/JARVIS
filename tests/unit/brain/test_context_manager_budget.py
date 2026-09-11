"""
Unit tests for ContextManager and token prioritization.
"""

import pytest
from jarvis.brain.context import ContextManager
from jarvis.brain.models import ChatMessage


def test_context_manager_prompt_building():
    cm = ContextManager(max_context_tokens=1000)
    req = cm.build_generation_request(
        user_prompt="Explain local AI models.",
        history=[ChatMessage(role="user", content="Hi"), ChatMessage(role="assistant", content="Hello Boss.")],
        tool_contract="Available tools: filesystem.search",
        relevant_memory=["User prefers local inference."]
    )

    assert len(req.messages) > 0
    assert req.prompt == "Explain local AI models."
    assert any("User prefers local inference" in m.content for m in req.messages)


def test_context_manager_budget_trimming():
    cm = ContextManager(max_context_tokens=1500)
    history = [ChatMessage(role="user", content=f"Old turn {i} " * 50) for i in range(10)]

    req = cm.build_generation_request(
        user_prompt="Latest request",
        history=history,
        max_response_tokens=200
    )

    assert req.messages[-1].content == "Latest request"
    total_tokens = sum(cm.estimate_tokens(m.content) for m in req.messages)
    assert total_tokens <= 1500


def test_context_manager_category_prompts():
    cm = ContextManager(max_context_tokens=2000)
    prompt_text = cm.get_category_prompt("security")
    assert "Permission Boundary Guidelines" in prompt_text or "Safety Policy Guidelines" in prompt_text

    req = cm.build_generation_request(
        user_prompt="Run command",
        prompt_categories=["security", "execution"]
    )
    assert any("Permission Boundary Guidelines" in m.content or "Tool Execution Guidelines" in m.content for m in req.messages)


