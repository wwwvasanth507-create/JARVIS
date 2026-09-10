"""
Skill Workflow Planner for JARVIS.
"""

from typing import Any, Dict, List, Optional
from jarvis.core.orchestration.intent import Intent
from jarvis.core.orchestration.plan import Plan, PlanStep
from jarvis.security.permissions import PermissionCategory, RiskLevel
from jarvis.skills.models import SkillDefinition


class SkillPlanner:
    """Converts SkillDefinition workflow steps into Plan objects."""

    def create_skill_plan(
        self,
        skill: SkillDefinition,
        intent: Intent,
        registered_tools: Dict[str, Any],
    ) -> Plan:
        steps: List[PlanStep] = []
        step_id_map: Dict[str, str] = {}

        eff_risk = skill.effective_risk_level or skill.risk_level
        perm = skill.permissions[0] if skill.permissions else PermissionCategory.SYSTEM_CONTROL

        for wstep in skill.workflow:
            # Resolve tool metadata
            tool_obj = registered_tools.get(wstep.action)
            step_perm = perm
            step_risk = eff_risk
            if tool_obj and hasattr(tool_obj, "metadata"):
                step_perm = tool_obj.metadata.permission_requirement
                step_risk = tool_obj.metadata.risk_level

            args = dict(wstep.arguments)
            args.update(intent.parameters)

            # Map dependencies
            deps = [step_id_map[d] for d in wstep.depends_on if d in step_id_map]

            pstep = PlanStep(
                description=wstep.description or f"Execute {wstep.action}",
                tool_name=wstep.action,
                arguments=args,
                dependencies=deps,
                risk_level=step_risk,
                permission=step_perm,
            )
            step_id_map[wstep.id] = pstep.step_id
            steps.append(pstep)

        if not steps:
            # Fallback single step
            pstep = PlanStep(
                description=f"Skill '{skill.name}' execution",
                tool_name=intent.action,
                arguments=intent.parameters,
                risk_level=eff_risk,
                permission=perm,
            )
            steps.append(pstep)

        return Plan(goal_id=f"skill_{skill.skill_id}", steps=steps)
