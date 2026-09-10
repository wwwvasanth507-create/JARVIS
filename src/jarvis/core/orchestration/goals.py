"""
Goal Representation and Resolution for JARVIS.
"""

import uuid
from typing import Any, Dict, List
from pydantic import BaseModel, Field
from jarvis.core.orchestration.intent import Intent
from jarvis.security.permissions import RiskLevel


class Goal(BaseModel):
    goal_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    description: str
    success_conditions: List[str] = Field(default_factory=list)
    constraints: Dict[str, Any] = Field(default_factory=dict)
    priority: int = 1
    risk_level: RiskLevel = RiskLevel.LOW
    status: str = "PENDING"


class GoalResolver:
    """Converts structured Intents into Goal objects."""

    def resolve(self, intent: Intent) -> Goal:
        desc = f"Execute action '{intent.action}'"
        if intent.target:
            desc += f" on target '{intent.target}'"

        conditions = [f"Tool '{intent.action}' executed successfully"]
        if "open" in intent.action:
            conditions.append(f"Target '{intent.target}' state verified as running/active")
        elif "close" in intent.action:
            conditions.append(f"Target '{intent.target}' state verified as stopped")
        elif "search" in intent.action or "find" in intent.action:
            conditions.append("Query results returned and formatted")

        return Goal(
            description=desc,
            success_conditions=conditions,
            constraints=intent.constraints,
            risk_level=intent.risk_level,
            status="PENDING",
        )
