"""
Unit tests for Resource & Path Resolver.
"""

from pathlib import Path
from jarvis.utils.paths import ResourcePathResolver


def test_resource_path_resolver_root_dir():
    root = ResourcePathResolver.get_root_dir()
    assert isinstance(root, Path)
    assert root.exists()
    assert (root / "pyproject.toml").exists() or (root / "config").exists() or root == Path.cwd().resolve()


def test_resource_path_resolver_dirs():
    cfg_dir = ResourcePathResolver.get_config_dir()
    assert isinstance(cfg_dir, Path)
    assert cfg_dir.name == "config"

    data_dir = ResourcePathResolver.get_data_dir()
    assert isinstance(data_dir, Path)
    assert data_dir.name == "data"

    cache_dir = ResourcePathResolver.get_cache_dir()
    assert isinstance(cache_dir, Path)
    assert cache_dir.name == "cache"

    logs_dir = ResourcePathResolver.get_logs_dir()
    assert isinstance(logs_dir, Path)
    assert logs_dir.name == "logs"


def test_resolve_resource_relative_and_absolute(tmp_path):
    rel_path = ResourcePathResolver.resolve_resource("config/config.yaml")
    assert isinstance(rel_path, Path)

    abs_file = tmp_path / "dummy.txt"
    abs_file.write_text("test")
    resolved_abs = ResourcePathResolver.resolve_resource(str(abs_file))
    assert resolved_abs == abs_file
