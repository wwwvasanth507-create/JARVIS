"""
Autonomous Agent Loop State Machine for JARVIS.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AgentLoopStage(str, Enum):
    USER_REQUEST = "USER_REQUEST"
    UNDERSTAND = "UNDERSTAND"
    CREATE_GOAL = "CREATE_GOAL"
    RETRIEVE_KNOWLEDGE = "RETRIEVE_KNOWLEDGE"
    CREATE_PLAN = "CREATE_PLAN"
    CHECK_PERMISSIONS = "CHECK_PERMISSIONS"
    EXECUTE_ACTION = "EXECUTE_ACTION"
    OBSERVE_RESULT = "OBSERVE_RESULT"
    VERIFY = "VERIFY"
    RECOVER = "RECOVER"
    REPLAN = "REPLAN"
    RESPOND = "RESPOND"


class PlanStep(BaseModel):
    step_number: int
    description: str
    tool_name: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    permission_checked: bool = False
    executed: bool = False
    verified: bool = False
    output: Optional[Any] = None


class AgentLoopContext(BaseModel):
    request_id: str
    user_prompt: str
    stage: AgentLoopStage = AgentLoopStage.USER_REQUEST
    goal: Optional[str] = None
    plan: List[PlanStep] = Field(default_factory=list)
    current_step_index: int = 0
    retrieved_knowledge: List[str] = Field(default_factory=list)
    execution_attempts: int = 0
    max_recovery_attempts: int = 3
    is_completed: bool = False
    final_response: Optional[str] = None


class AgentLoopTracker:
    """Manages state transitions in the autonomous loop for JARVIS."""

    def __init__(self, context: AgentLoopContext):
        self.context = context

    def transition_to(self, new_stage: AgentLoopStage) -> None:
        self.context.stage = new_stage

    def mark_completed(self, response: str) -> None:
        self.context.is_completed = True
        self.context.final_response = response
        self.transition_to(AgentLoopStage.RESPOND)
