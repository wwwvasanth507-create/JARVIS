"""
Data models and Enums for JARVIS Skill subsystem.
"""

import time
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from jarvis.security.permissions import PermissionCategory, RiskLevel


class SkillCategory(str, Enum):
    BUILTIN = "builtin"
    SYSTEM = "system"
    USER = "user"
    EXPERIMENTAL = "experimental"


class SkillLifecycleState(str, Enum):
    DISCOVERED = "DISCOVERED"
    VALIDATED = "VALIDATED"
    REGISTERED = "REGISTERED"
    ENABLED = "ENABLED"
    DISABLED = "DISABLED"
    FAILED = "FAILED"
    UNAVAILABLE = "UNAVAILABLE"


class SkillWorkflowStep(BaseModel):
    id: str
    action: str
    description: str = ""
    depends_on: List[str] = Field(default_factory=list)
    arguments: Dict[str, Any] = Field(default_factory=dict)


class SkillDefinition(BaseModel):
    skill_id: str
    name: str
    display_name: Optional[str] = None
    description: str
    version: str = "1.0.0"
    author: str = "JARVIS Core"
    category: SkillCategory = SkillCategory.BUILTIN
    aliases: List[str] = Field(default_factory=list)
    intents: List[str] = Field(default_factory=list)
    tools: List[str] = Field(default_factory=list)
    workflow: List[SkillWorkflowStep] = Field(default_factory=list)
    permissions: List[PermissionCategory] = Field(default_factory=list)
    risk_level: RiskLevel = RiskLevel.LOW
    effective_risk_level: Optional[RiskLevel] = None
    dependencies: List[str] = Field(default_factory=list)
    state: SkillLifecycleState = SkillLifecycleState.DISCOVERED
    manifest_path: Optional[str] = None
    enabled_at: Optional[float] = None

    def model_post_init(self, __context: Any) -> None:
        if not self.display_name:
            self.display_name = self.name


class SkillQueryResult(BaseModel):
    skill_id: str
    name: str
    description: str
    category: SkillCategory
    state: SkillLifecycleState
    enabled: bool
    risk_level: RiskLevel
