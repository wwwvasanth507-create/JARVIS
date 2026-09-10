"""
Application Registry for JARVIS.
Loads config/applications.yaml, maintains application metadata, and resolves query aliases.
"""

from pathlib import Path
from typing import Dict, List, Optional
import yaml
import logging

from jarvis.applications.models import ApplicationEntry

logger = logging.getLogger("jarvis.applications.registry")


class ApplicationRegistry:
    """Registry maintaining application alias mappings and executable metadata."""

    def __init__(self, config_path: Optional[str | Path] = None):
        self.config_path = Path(config_path) if config_path else Path("config/applications.yaml")
        self.entries: Dict[str, ApplicationEntry] = {}
        self._load_registry()

    def _load_registry(self) -> None:
        if not self.config_path.exists():
            logger.warning(f"Application registry file not found at '{self.config_path}'")
            return

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
                apps_data = data.get("applications", {})

                for key, app_info in apps_data.items():
                    entry = ApplicationEntry(
                        name=app_info.get("name", key),
                        aliases=app_info.get("aliases", [key]),
                        executable=app_info.get("executable", f"{key}.exe"),
                        common_paths=app_info.get("common_paths", []),
                    )
                    self.entries[key.lower()] = entry
        except Exception as e:
            logger.error(f"Failed to load application registry: {e}")

    def resolve(self, query: str) -> Optional[ApplicationEntry]:
        """Resolves application query or alias (e.g. 'chrome' or 'google chrome') to ApplicationEntry."""
        if not query:
            return None

        clean_query = query.strip().lower()

        # Direct key match
        if clean_query in self.entries:
            return self.entries[clean_query]

        # Alias match
        for entry in self.entries.values():
            if clean_query == entry.name.lower() or clean_query == entry.executable.lower():
                return entry
            for alias in entry.aliases:
                if clean_query == alias.lower():
                    return entry

        # Partial match
        for entry in self.entries.values():
            if clean_query in entry.name.lower() or clean_query in entry.executable.lower():
                return entry
            for alias in entry.aliases:
                if clean_query in alias.lower():
                    return entry

        # Fallback entry for generic executable query
        return ApplicationEntry(
            name=query,
            aliases=[clean_query],
            executable=clean_query if clean_query.endswith(".exe") else f"{clean_query}.exe",
            common_paths=[],
        )

    def list_applications(self) -> List[ApplicationEntry]:
        return list(self.entries.values())
