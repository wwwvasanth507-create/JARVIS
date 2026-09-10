"""
Semantic Versioning Manager for JARVIS Skills.
"""

from typing import Tuple


class SkillVersionManager:
    """Manages semantic version comparison for skills."""

    def parse_version(self, version_str: str) -> Tuple[int, int, int]:
        parts = version_str.split(".")
        if len(parts) != 3:
            return (1, 0, 0)
        try:
            return (int(parts[0]), int(parts[1]), int(parts[2]))
        except ValueError:
            return (1, 0, 0)

    def is_compatible(self, v1: str, v2: str) -> bool:
        major1, _, _ = self.parse_version(v1)
        major2, _, _ = self.parse_version(v2)
        # Same major version means backwards compatible
        return major1 == major2
