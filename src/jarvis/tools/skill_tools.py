"""
Structured Skill Tools for JARVIS Tool Subsystem.
"""

from typing import Any, Dict, Optional
from jarvis.security.permissions import PermissionCategory, RiskLevel
from jarvis.tools.base import BaseTool, ToolMetadata, ToolResult


def _get_skill_manager(custom_mgr: Optional[Any] = None) -> Any:
    if custom_mgr is not None:
        return custom_mgr
    from jarvis.skills.manager import SkillManager
    return SkillManager()


class ListSkillsTool(BaseTool):
    def __init__(self, manager: Optional[Any] = None):
        self.mgr = manager
        super().__init__(
            ToolMetadata(
                name="skill.list",
                description="List all registered skills and their enabled states.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "category": {"type": "string", "enum": ["builtin", "system", "user", "experimental"]},
                        "enabled_only": {"type": "boolean", "default": False},
                    },
                },
                permission_requirement=PermissionCategory.SYSTEM_CONTROL,
                risk_level=RiskLevel.LOW,
                verification_strategy="skills_listed",
            )
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        try:
            mgr = _get_skill_manager(self.mgr)
            res = mgr.list_query_results()
            data = [r.model_dump() for r in res]
            return ToolResult(success=True, data=data)
        except Exception as e:
            return self.handle_error(e)

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class FindSkillTool(BaseTool):
    def __init__(self, manager: Optional[Any] = None):
        self.mgr = manager
        super().__init__(
            ToolMetadata(
                name="skill.find",
                description="Find skills matching query or alias.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query or skill alias"},
                    },
                    "required": ["query"],
                },
                permission_requirement=PermissionCategory.SYSTEM_CONTROL,
                risk_level=RiskLevel.LOW,
                verification_strategy="skill_found",
            )
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        try:
            mgr = _get_skill_manager(self.mgr)
            q = kwargs["query"].lower()
            all_skills = mgr.list_skills()
            matches = []
            for s in all_skills:
                if q in s.skill_id.lower() or q in s.name.lower() or any(q in a.lower() for a in s.aliases):
                    matches.append(s.model_dump())
            return ToolResult(success=True, data=matches)
        except Exception as e:
            return self.handle_error(e)

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class SkillInfoTool(BaseTool):
    def __init__(self, manager: Optional[Any] = None):
        self.mgr = manager
        super().__init__(
            ToolMetadata(
                name="skill.info",
                description="Get detailed manifest and workflow information for a skill.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "skill_id": {"type": "string", "description": "Target skill ID"},
                    },
                    "required": ["skill_id"],
                },
                permission_requirement=PermissionCategory.SYSTEM_CONTROL,
                risk_level=RiskLevel.LOW,
                verification_strategy="skill_info_retrieved",
            )
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        try:
            mgr = _get_skill_manager(self.mgr)
            skill = mgr.get_skill(kwargs["skill_id"])
            if not skill:
                return ToolResult(success=False, error=f"Skill '{kwargs['skill_id']}' not found.")
            return ToolResult(success=True, data=skill.model_dump())
        except Exception as e:
            return self.handle_error(e)

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class EnableSkillTool(BaseTool):
    def __init__(self, manager: Optional[Any] = None):
        self.mgr = manager
        super().__init__(
            ToolMetadata(
                name="skill.enable",
                description="Enable a registered skill.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "skill_id": {"type": "string", "description": "Target skill ID to enable"},
                    },
                    "required": ["skill_id"],
                },
                permission_requirement=PermissionCategory.SYSTEM_CONTROL,
                risk_level=RiskLevel.MEDIUM,
                verification_strategy="skill_enabled",
            )
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        try:
            mgr = _get_skill_manager(self.mgr)
            skill = mgr.enable_skill(kwargs["skill_id"])
            return ToolResult(success=True, data=skill.model_dump())
        except Exception as e:
            return self.handle_error(e)

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class DisableSkillTool(BaseTool):
    def __init__(self, manager: Optional[Any] = None):
        self.mgr = manager
        super().__init__(
            ToolMetadata(
                name="skill.disable",
                description="Disable an active skill.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "skill_id": {"type": "string", "description": "Target skill ID to disable"},
                    },
                    "required": ["skill_id"],
                },
                permission_requirement=PermissionCategory.SYSTEM_CONTROL,
                risk_level=RiskLevel.MEDIUM,
                verification_strategy="skill_disabled",
            )
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        try:
            mgr = _get_skill_manager(self.mgr)
            skill = mgr.disable_skill(kwargs["skill_id"])
            return ToolResult(success=True, data=skill.model_dump())
        except Exception as e:
            return self.handle_error(e)

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class SkillStatusTool(BaseTool):
    def __init__(self, manager: Optional[Any] = None):
        self.mgr = manager
        super().__init__(
            ToolMetadata(
                name="skill.status",
                description="Check current lifecycle state and effective risk of a skill.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "skill_id": {"type": "string", "description": "Target skill ID"},
                    },
                    "required": ["skill_id"],
                },
                permission_requirement=PermissionCategory.SYSTEM_CONTROL,
                risk_level=RiskLevel.LOW,
                verification_strategy="skill_status_checked",
            )
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        try:
            mgr = _get_skill_manager(self.mgr)
            skill = mgr.get_skill(kwargs["skill_id"])
            if not skill:
                return ToolResult(success=False, error=f"Skill '{kwargs['skill_id']}' not found.")
            info = {
                "skill_id": skill.skill_id,
                "name": skill.name,
                "state": skill.state.value if hasattr(skill.state, "value") else str(skill.state),
                "effective_risk_level": skill.effective_risk_level.value if skill.effective_risk_level else skill.risk_level.value,
                "tools_count": len(skill.tools),
            }
            return ToolResult(success=True, data=info)
        except Exception as e:
            return self.handle_error(e)

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


SKILL_TOOLS = [
    ListSkillsTool(),
    FindSkillTool(),
    SkillInfoTool(),
    EnableSkillTool(),
    DisableSkillTool(),
    SkillStatusTool(),
]
