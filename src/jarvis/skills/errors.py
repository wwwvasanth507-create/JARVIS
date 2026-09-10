"""
Skill Subsystem Error Hierarchy for JARVIS.
"""


class SkillError(Exception):
    """Base exception for all skill subsystem errors."""
    pass


class SkillManifestError(SkillError):
    """Raised when skill manifest YAML parsing fails."""
    pass


class SkillValidationError(SkillError):
    """Raised when skill definition fails schema validation."""
    def __init__(self, message: str, skill_id: str | None = None, violations: list[str] | None = None):
        super().__init__(message)
        self.skill_id = skill_id
        self.violations = violations or []


class SkillNotFoundError(SkillError):
    """Raised when requested skill is not registered or found."""
    pass


class AmbiguousSkillError(SkillError):
    """Raised when multiple skills match an intent ambivalently."""
    def __init__(self, message: str, candidates: list[str] | None = None):
        super().__init__(message)
        self.candidates = candidates or []


class SkillDependencyError(SkillError):
    """Raised when required tools or subsystems for a skill are missing."""
    pass


class SkillDisabledError(SkillError):
    """Raised when attempting to execute a disabled skill."""
    pass


class SkillPermissionDeniedError(SkillError):
    """Raised when a skill demands unpermitted security categories."""
    pass
