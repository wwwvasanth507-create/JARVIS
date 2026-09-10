"""
Centralized Resource & Path Resolution Utilities for JARVIS.

Handles path normalization across:
1. Source checkout execution
2. Installed python package site-packages
3. PyInstaller frozen standalone binary (sys._MEIPASS)
"""

import sys
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ResourcePathResolver:
    """Resolves resource and data paths relative to runtime execution context."""

    _root_path_cache = None

    @classmethod
    def get_root_dir(cls) -> Path:
        """Returns authoritative root path of project / binary bundle."""
        if cls._root_path_cache is not None:
            return cls._root_path_cache

        if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
            # Frozen PyInstaller executable
            cls._root_path_cache = Path(sys._MEIPASS).resolve()
        else:
            # Source directory execution (c:\ll\JARVIS)
            # Find root by traversing up until pyproject.toml or config/ is found
            current = Path(__file__).resolve().parent
            while current.parent != current:
                if (current / "pyproject.toml").exists() or (current / "config").exists():
                    cls._root_path_cache = current
                    return cls._root_path_cache
                current = current.parent
            cls._root_path_cache = Path.cwd().resolve()

        return cls._root_path_cache

    @classmethod
    def get_config_dir(cls) -> Path:
        p = cls.get_root_dir() / "config"
        if not p.exists():
            p.mkdir(parents=True, exist_ok=True)
        return p

    @classmethod
    def get_data_dir(cls) -> Path:
        p = cls.get_root_dir() / "data"
        if not p.exists():
            p.mkdir(parents=True, exist_ok=True)
        return p

    @classmethod
    def get_cache_dir(cls) -> Path:
        p = cls.get_data_dir() / "cache"
        if not p.exists():
            p.mkdir(parents=True, exist_ok=True)
        return p

    @classmethod
    def get_logs_dir(cls) -> Path:
        p = cls.get_root_dir() / "logs"
        if not p.exists():
            p.mkdir(parents=True, exist_ok=True)
        return p

    @classmethod
    def get_skills_dir(cls) -> Path:
        return cls.get_root_dir() / "skills"

    @classmethod
    def resolve_resource(cls, relative_path: str) -> Path:
        """Resolves a relative path to absolute location based on runtime environment."""
        p = Path(relative_path)
        if p.is_absolute():
            return p
        return (cls.get_root_dir() / relative_path).resolve()
