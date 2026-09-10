"""
Planner component for JARVIS orchestration.
"""

from typing import Any, Dict, List, Optional
from jarvis.core.orchestration.goals import Goal
from jarvis.core.orchestration.intent import Intent
from jarvis.core.orchestration.plan import Plan, PlanStep, PlanStepStatus
from jarvis.security.permissions import PermissionCategory, RiskLevel


class Planner:
    """Constructs structured Plan objects from Intents and Goals."""

    TOOL_PERMISSION_MAP: Dict[str, tuple[PermissionCategory, RiskLevel]] = {
        # Application
        "application.list": (PermissionCategory.APPLICATION_CONTROL, RiskLevel.LOW),
        "application.find": (PermissionCategory.APPLICATION_CONTROL, RiskLevel.LOW),
        "application.is_running": (PermissionCategory.APPLICATION_CONTROL, RiskLevel.LOW),
        "application.list_running": (PermissionCategory.APPLICATION_CONTROL, RiskLevel.LOW),
        "application.health": (PermissionCategory.APPLICATION_CONTROL, RiskLevel.LOW),
        "application.list_startup": (PermissionCategory.APPLICATION_CONTROL, RiskLevel.LOW),
        "application.open": (PermissionCategory.APPLICATION_CONTROL, RiskLevel.MEDIUM),
        "application.focus": (PermissionCategory.APPLICATION_CONTROL, RiskLevel.MEDIUM),
        "application.open_file": (PermissionCategory.APPLICATION_CONTROL, RiskLevel.MEDIUM),
        "application.open_url": (PermissionCategory.APPLICATION_CONTROL, RiskLevel.MEDIUM),
        "application.close": (PermissionCategory.APPLICATION_CONTROL, RiskLevel.HIGH),
        "application.restart": (PermissionCategory.APPLICATION_CONTROL, RiskLevel.HIGH),
        
        # Filesystem
        "filesystem.list_directory": (PermissionCategory.READ_FILES, RiskLevel.LOW),
        "filesystem.read_file": (PermissionCategory.READ_FILES, RiskLevel.LOW),
        "filesystem.search": (PermissionCategory.READ_FILES, RiskLevel.LOW),
        "filesystem.get_metadata": (PermissionCategory.READ_FILES, RiskLevel.LOW),
        "filesystem.write_file": (PermissionCategory.WRITE_FILES, RiskLevel.MEDIUM),
        "filesystem.create_directory": (PermissionCategory.WRITE_FILES, RiskLevel.MEDIUM),
        "filesystem.copy": (PermissionCategory.WRITE_FILES, RiskLevel.MEDIUM),
        "filesystem.move": (PermissionCategory.WRITE_FILES, RiskLevel.MEDIUM),
        "filesystem.rename": (PermissionCategory.WRITE_FILES, RiskLevel.MEDIUM),
        "filesystem.delete": (PermissionCategory.DELETE_FILES, RiskLevel.HIGH),
        
        # Computer
        "computer.list_windows": (PermissionCategory.SCREEN_READ, RiskLevel.LOW),
        "computer.get_active_window": (PermissionCategory.SCREEN_READ, RiskLevel.LOW),
        "computer.focus_window": (PermissionCategory.COMPUTER_CONTROL, RiskLevel.MEDIUM),
        "computer.press_key": (PermissionCategory.COMPUTER_CONTROL, RiskLevel.MEDIUM),
        "computer.click_mouse": (PermissionCategory.COMPUTER_CONTROL, RiskLevel.MEDIUM),
        
        # Browser
        "browser.open": (PermissionCategory.BROWSER_CONTROL, RiskLevel.LOW),
        "browser.search": (PermissionCategory.BROWSER_CONTROL, RiskLevel.LOW),
        "browser.get_text": (PermissionCategory.BROWSER_CONTROL, RiskLevel.LOW),
        
        # Shell
        "shell.execute": (PermissionCategory.RUN_COMMANDS, RiskLevel.HIGH),
    }

    def create_plan(self, intent: Intent, goal: Goal) -> Plan:
        if intent.is_fast_path and intent.direct_tool_name:
            perm, risk = self.TOOL_PERMISSION_MAP.get(
                intent.direct_tool_name,
                (PermissionCategory.SYSTEM_CONTROL, intent.risk_level),
            )
            step = PlanStep(
                description=goal.description,
                tool_name=intent.direct_tool_name,
                arguments=intent.parameters,
                risk_level=risk,
                permission=perm,
                success_condition=goal.success_conditions[0] if goal.success_conditions else "succeeded",
            )
            return Plan(
                goal_id=goal.goal_id,
                steps=[step],
            )

        # Multi-step handling heuristics based on request intent target/action
        steps: List[PlanStep] = []
        
        if "latest" in intent.target.lower() if intent.target else False:
            # Multi-step: Step 1 search files, Step 2 open candidate
            step1 = PlanStep(
                description="Search allowed directory for candidate files",
                tool_name="filesystem.search",
                arguments={"query": intent.parameters.get("query", "*")},
                risk_level=RiskLevel.LOW,
                permission=PermissionCategory.READ_FILES,
            )
            step2 = PlanStep(
                description="Open candidate file with default application",
                tool_name="application.open_file",
                arguments={},
                dependencies=[step1.step_id],
                risk_level=RiskLevel.MEDIUM,
                permission=PermissionCategory.APPLICATION_CONTROL,
            )
            steps.extend([step1, step2])
        else:
            perm, risk = self.TOOL_PERMISSION_MAP.get(
                intent.action,
                (PermissionCategory.SYSTEM_CONTROL, intent.risk_level),
            )
            step = PlanStep(
                description=goal.description,
                tool_name=intent.action if intent.action != "general.task" else "application.find",
                arguments=intent.parameters,
                risk_level=risk,
                permission=perm,
            )
            steps.append(step)

        return Plan(
            goal_id=goal.goal_id,
            steps=steps,
        )
