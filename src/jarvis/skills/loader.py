"""
Skill Loader and Verification Manager for JARVIS.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
from jarvis.skills.dependencies import SkillDependencyManager
from jarvis.skills.errors import SkillError
from jarvis.skills.manifest import SkillManifestParser
from jarvis.skills.models import SkillDefinition, SkillLifecycleState
from jarvis.skills.safety import SkillSafetyPolicy
from jarvis.skills.validator import SkillValidator


class SkillLoader:
    """Loads and validates skills without arbitrary code execution."""

    def __init__(
        self,
        parser: Optional[SkillManifestParser] = None,
        validator: Optional[SkillValidator] = None,
        dep_mgr: Optional[SkillDependencyManager] = None,
        safety_policy: Optional[SkillSafetyPolicy] = None,
    ):
        self.parser = parser or SkillManifestParser()
        self.validator = validator or SkillValidator()
        self.dep_mgr = dep_mgr or SkillDependencyManager()
        self.safety_policy = safety_policy or SkillSafetyPolicy()

    def load_skill(
        self,
        manifest_path: str | Path,
        registered_tools: Dict[str, Any],
    ) -> SkillDefinition:
        # 1. Parse YAML manifest
        skill = self.parser.parse_file(manifest_path)

        # 2. Check tool dependencies
        deps_met, missing = self.dep_mgr.evaluate_dependencies(skill, registered_tools)
        if not deps_met:
            skill.state = SkillLifecycleState.UNAVAILABLE
            return skill

        # 3. Structural schema validation
        try:
            self.validator.validate(skill, registered_tools)
        except SkillError:
            skill.state = SkillLifecycleState.FAILED
            raise

        # 4. Compute effective risk escalation
        self.safety_policy.compute_effective_risk(skill, registered_tools)

        skill.state = SkillLifecycleState.VALIDATED
        return skill
