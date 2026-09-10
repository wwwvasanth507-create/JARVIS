"""
Context Compression and Management for JARVIS orchestration.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class OrchestrationContext(BaseModel):
    """Bounded, memory-efficient context representation."""

    request: str
    intent_summary: Optional[str] = None
    goal_summary: Optional[str] = None
    step_summaries: List[str] = Field(default_factory=list)
    recent_observations: List[Dict[str, Any]] = Field(default_factory=list)
    max_recent_observations: int = 5

    def add_step_summary(self, summary: str) -> None:
        self.step_summaries.append(summary)

    def add_observation(self, observation: Dict[str, Any]) -> None:
        self.recent_observations.append(observation)
        if len(self.recent_observations) > self.max_recent_observations:
            self.recent_observations.pop(0)

    def compress(self) -> Dict[str, Any]:
        return {
            "request": self.request,
            "intent": self.intent_summary,
            "goal": self.goal_summary,
            "completed_steps_count": len(self.step_summaries),
            "recent_observations": self.recent_observations,
        }
