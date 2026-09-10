"""
Skill Manifest Parser for JARVIS.
"""

from pathlib import Path
from typing import Any, Dict, Optional
import yaml
from jarvis.security.permissions import PermissionCategory, RiskLevel
from jarvis.skills.errors import SkillManifestError
from jarvis.skills.models import SkillCategory, SkillDefinition, SkillLifecycleState, SkillWorkflowStep


class SkillManifestParser:
    """Parses skill.yaml manifest files into SkillDefinition instances."""

    def parse_file(self, manifest_path: str | Path) -> SkillDefinition:
        path = Path(manifest_path)
        if not path.exists():
            raise SkillManifestError(f"Manifest file not found at {path}")

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
        except Exception as e:
            raise SkillManifestError(f"Failed to parse YAML manifest at {path}: {e}")

        return self.parse_dict(data, manifest_path=str(path))

    def parse_dict(self, data: Dict[str, Any], manifest_path: Optional[str] = None) -> SkillDefinition:
        skill_data = data.get("skill", {})
        if not skill_data:
            raise SkillManifestError("Missing top-level 'skill' key in manifest.")

        skill_id = skill_data.get("id")
        name = skill_data.get("name")
        description = skill_data.get("description", "")
        if not skill_id or not name:
            raise SkillManifestError("Manifest 'skill' block must include 'id' and 'name'.")

        category_str = skill_data.get("category", "builtin")
        try:
            category = SkillCategory(category_str)
        except ValueError:
            category = SkillCategory.BUILTIN

        risk_str = skill_data.get("risk_level", "LOW")
        try:
            risk_level = RiskLevel(risk_str)
        except ValueError:
            risk_level = RiskLevel.LOW

        # Parse permissions
        perm_list = []
        for p in skill_data.get("permissions", []):
            try:
                perm_list.append(PermissionCategory(p))
            except ValueError:
                pass

        # Parse workflow
        workflow_steps = []
        for step_data in data.get("workflow", []):
            workflow_steps.append(
                SkillWorkflowStep(
                    id=step_data.get("id", "step"),
                    action=step_data.get("action", ""),
                    description=step_data.get("description", ""),
                    depends_on=step_data.get("depends_on", []),
                    arguments=step_data.get("arguments", {}),
                )
            )

        enabled = skill_data.get("enabled", True)
        initial_state = SkillLifecycleState.VALIDATED if enabled else SkillLifecycleState.DISABLED

        return SkillDefinition(
            skill_id=skill_id,
            name=name,
            display_name=skill_data.get("display_name"),
            description=description,
            version=skill_data.get("version", "1.0.0"),
            author=skill_data.get("author", "JARVIS Core"),
            category=category,
            aliases=skill_data.get("aliases", []),
            intents=skill_data.get("intents", []),
            tools=skill_data.get("tools", []),
            workflow=workflow_steps,
            permissions=perm_list,
            risk_level=risk_level,
            dependencies=skill_data.get("dependencies", []),
            state=initial_state,
            manifest_path=manifest_path,
        )
