"""
Application Registry maintaining metadata, alias resolution, category groups, and cache indexing for JARVIS.
"""

from pathlib import Path
from typing import Dict, List, Optional, Union
import yaml

from jarvis.applications.aliases import AliasResolver
from jarvis.applications.discovery import ApplicationDiscovery
from jarvis.applications.errors import ApplicationNotFound, AmbiguousApplication
from jarvis.applications.platform import ApplicationPlatform
from jarvis.applications.state import ApplicationInfo


class ApplicationRegistry:
    """Central application registry holding profile mappings and category groups."""

    def __init__(
        self,
        config_path: Optional[Union[str, Path]] = None,
        cache_path: Optional[Union[str, Path]] = None,
    ):
        self.config_path = Path(config_path) if config_path else Path("config/applications.yaml")
        self.entries: Dict[str, ApplicationInfo] = {}
        self.groups: Dict[str, List[str]] = {}
        self.protected_apps: List[str] = []
        self.discovery = ApplicationDiscovery(cache_file=Path(cache_path) if cache_path else None)

        self._load_config()
        self._sync_discovery_cache()

    def _load_config(self) -> None:
        if not self.config_path.exists():
            return

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
                apps_cfg = data.get("applications", {})
                self.groups = data.get("groups", {})
                self.protected_apps = data.get("protected_applications", [])

                for key, info in apps_cfg.items():
                    key_lower = key.lower()
                    app_info = ApplicationInfo(
                        name=info.get("name", key),
                        display_name=info.get("display_name", info.get("name", key)),
                        category=info.get("category", "utilities"),
                        aliases=info.get("aliases", [key_lower]),
                        executable=info.get("executable", f"{key}.exe"),
                        common_paths=info.get("common_paths", []),
                        startup_timeout=info.get("startup_timeout", 15),
                        platform=ApplicationPlatform.get_platform_name(),
                    )
                    # Resolve path if available
                    exp_path = ApplicationPlatform.resolve_executable_path(app_info)
                    if exp_path:
                        app_info.executable_path = str(exp_path)

                    self.entries[key_lower] = app_info
        except Exception:
            pass

    def _sync_discovery_cache(self) -> None:
        cache = self.discovery.load_cache()
        if cache and cache.applications:
            for cached_app in cache.applications:
                k = cached_app.name.lower()
                if k in self.entries:
                    if cached_app.executable_path:
                        self.entries[k].executable_path = cached_app.executable_path

    def refresh_discovery(self) -> List[ApplicationInfo]:
        """Triggers OS application discovery scan and updates cache."""
        discovered = self.discovery.discover_applications(list(self.entries.values()))
        for disc in discovered:
            k = disc.name.lower()
            if k in self.entries:
                self.entries[k] = disc
        return list(self.entries.values())

    def resolve(self, query: str) -> ApplicationInfo:
        """Resolves application query or alias using AliasResolver."""
        return AliasResolver.resolve(query, self.entries)

    def list_applications(self) -> List[ApplicationInfo]:
        """Lists all registered applications."""
        return list(self.entries.values())

    def get_group_applications(self, group_name: str) -> List[ApplicationInfo]:
        """Returns applications belonging to a group (e.g. 'development', 'browsers')."""
        group_keys = self.groups.get(group_name.lower(), [])
        result = []
        for k in group_keys:
            if k.lower() in self.entries:
                result.append(self.entries[k.lower()])
        return result
