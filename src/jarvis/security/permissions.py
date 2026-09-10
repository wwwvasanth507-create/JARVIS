"""
Security and permission evaluation module for JARVIS.
"""

from enum import Enum
from pathlib import Path
from typing import Dict, Any, List, Optional
import yaml
from pydantic import BaseModel


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class PermissionCategory(str, Enum):
    READ_FILES = "READ_FILES"
    WRITE_FILES = "WRITE_FILES"
    DELETE_FILES = "DELETE_FILES"
    RUN_COMMANDS = "RUN_COMMANDS"
    BROWSER_CONTROL = "BROWSER_CONTROL"
    NETWORK_ACCESS = "NETWORK_ACCESS"
    APPLICATION_CONTROL = "APPLICATION_CONTROL"
    SYSTEM_CONTROL = "SYSTEM_CONTROL"
    COMPUTER_CONTROL = "COMPUTER_CONTROL"
    SCREEN_READ = "SCREEN_READ"


class PermissionCheckResult(BaseModel):
    allowed: bool
    risk_level: RiskLevel
    requires_boss_approval: bool
    reason: str


class PermissionEvaluator:
    """Evaluates requested tool actions against permissions.yaml policies."""

    RISK_HIERARCHY = {
        RiskLevel.LOW: 1,
        RiskLevel.MEDIUM: 2,
        RiskLevel.HIGH: 3,
        RiskLevel.CRITICAL: 4,
    }

    def __init__(self, permissions_file: Optional[str | Path] = None):
        self.permissions_file = Path(permissions_file) if permissions_file else None
        self.categories: Dict[str, Any] = {}
        self.risk_levels: Dict[str, Any] = {}
        self.prohibited_actions: List[str] = []
        self._load_policy()

    def _load_policy(self) -> None:
        if self.permissions_file and self.permissions_file.exists():
            with open(self.permissions_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
                self.categories = data.get("categories", {})
                self.risk_levels = data.get("risk_levels", {})
                self.prohibited_actions = data.get("policies", {}).get("prohibited_actions", [])

    def evaluate(
        self,
        category: PermissionCategory | str,
        risk_level: RiskLevel | str,
        action_name: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> PermissionCheckResult:
        cat_str = category.value if isinstance(category, PermissionCategory) else str(category)
        risk_enum = RiskLevel(risk_level) if isinstance(risk_level, str) else risk_level

        # Check prohibited actions
        if action_name in self.prohibited_actions:
            return PermissionCheckResult(
                allowed=False,
                risk_level=RiskLevel.CRITICAL,
                requires_boss_approval=True,
                reason=f"Action '{action_name}' is explicitly prohibited by security policy.",
            )

        # High or Critical risk requires Boss confirmation
        requires_approval = self.RISK_HIERARCHY[risk_enum] >= self.RISK_HIERARCHY[RiskLevel.HIGH]

        return PermissionCheckResult(
            allowed=True,
            risk_level=risk_enum,
            requires_boss_approval=requires_approval,
            reason=f"Action '{action_name}' under category '{cat_str}' evaluated at risk level {risk_enum.value}.",
        )
