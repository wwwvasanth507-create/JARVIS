"""
Application permission evaluator integrating with central JARVIS security framework.
"""

from pathlib import Path
from typing import Any, Dict, Optional, Union
from jarvis.security.permissions import PermissionCategory, PermissionEvaluator, RiskLevel
from jarvis.applications.errors import ApplicationPermissionDenied
from jarvis.applications.state import ApplicationInfo


class ApplicationPermissionChecker:
    """Evaluates security permission policies for application control actions."""

    def __init__(self, security_evaluator: Optional[PermissionEvaluator] = None):
        self.security_evaluator = security_evaluator or PermissionEvaluator()

    def evaluate_action(
        self,
        action: str,
        app_info: Optional[ApplicationInfo] = None,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> RiskLevel:
        """
        Evaluates permission for an application action.
        Returns assessed RiskLevel. Raises ApplicationPermissionDenied if rejected.
        """
        if action in ("list", "find", "is_running", "list_running", "health", "list_startup"):
            risk = RiskLevel.LOW
        elif action in ("open", "focus", "open_file", "open_url"):
            risk = RiskLevel.MEDIUM
        elif action in ("close", "restart"):
            risk = RiskLevel.HIGH
        else:
            risk = RiskLevel.HIGH

        params = parameters or {}
        if app_info:
            params["application"] = app_info.name
            params["executable"] = app_info.executable

        sec_res = self.security_evaluator.evaluate(
            category=PermissionCategory.APPLICATION_CONTROL,
            risk_level=risk,
            action_name=f"application.{action}",
            parameters=params,
        )

        if not sec_res.allowed:
            raise ApplicationPermissionDenied(sec_res.reason)

        return risk
