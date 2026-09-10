"""
Skill Directory Discovery for JARVIS.
"""

from pathlib import Path
from typing import List


class SkillDiscovery:
    """Discovers skill.yaml manifests across configured directories."""

    DEFAULT_DIRS = [
        "skills/builtin",
        "skills/system",
        "skills/user",
        "skills/experimental",
    ]

    def discover_manifest_paths(self, base_dirs: List[str] | None = None) -> List[Path]:
        dirs_to_scan = base_dirs or self.DEFAULT_DIRS
        found_paths = []

        for d_str in dirs_to_scan:
            d_path = Path(d_str)
            if d_path.exists() and d_path.is_dir():
                for manifest in d_path.rglob("skill.yaml"):
                    found_paths.append(manifest)

        return found_paths
