"""
Skill Definition Validator for JARVIS.
"""

import re
from typing import Any, Dict
from jarvis.skills.errors import SkillValidationError
from jarvis.skills.models import SkillDefinition


class SkillValidator:
    """Enforces integrity and structural schema checks on SkillDefinition models."""

    SKILL_ID_PATTERN = r"^[a-z0-9_]+$"
    VERSION_PATTERN = r"^\d+\.\d+\.\d+$"

    def validate(self, skill: SkillDefinition, registered_tools: Dict[str, Any]) -> None:
        violations = []

        # 1. Validate skill ID format
        if not re.match(self.SKILL_ID_PATTERN, skill.skill_id):
            violations.append(f"Invalid skill_id '{skill.skill_id}': must match pattern '{self.SKILL_ID_PATTERN}'.")

        # 2. Validate version
        if not re.match(self.VERSION_PATTERN, skill.version):
            violations.append(f"Invalid version '{skill.version}': must follow semantic versioning X.Y.Z.")

        # 3. Validate tools existence in registry
        for tool_name in skill.tools:
            if tool_name not in registered_tools:
                violations.append(f"Declared tool '{tool_name}' is not registered in system Tool Registry.")

        # 4. Validate workflow steps
        step_ids = {s.id for s in skill.workflow}
        for step in skill.workflow:
            if not step.action:
                violations.append(f"Workflow step '{step.id}' missing required action.")
            elif step.action not in registered_tools:
                violations.append(f"Workflow step '{step.id}' uses unregistered tool '{step.action}'.")

            for dep in step.depends_on:
                if dep not in step_ids:
                    violations.append(f"Workflow step '{step.id}' references unknown dependency step '{dep}'.")

        if violations:
            raise SkillValidationError(
                message=f"Skill validation failed for '{skill.skill_id}': {'; '.join(violations)}",
                skill_id=skill.skill_id,
                violations=violations,
            )
