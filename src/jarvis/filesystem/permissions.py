"""
Filesystem Security & Permission Evaluator for JARVIS.
"""

from pathlib import Path
from typing import Any, Dict, Optional, Union
import yaml

from jarvis.filesystem.errors import PermissionDenied, FilesystemUnavailable
from jarvis.filesystem.paths import PathResolver
from jarvis.filesystem.safety import SensitivityChecker
from jarvis.security.permissions import PermissionCategory, PermissionEvaluator, RiskLevel


class FilesystemPermissionChecker:
    """
    Evaluates filesystem actions against filesystem policy and central security evaluator.
    """

    def __init__(
        self,
        config_path: Optional[Union[str, Path]] = None,
        security_evaluator: Optional[PermissionEvaluator] = None,
    ):
        self.config_path = Path(config_path) if config_path else Path("config/filesystem.yaml")
        self.security_evaluator = security_evaluator or PermissionEvaluator()
        self.enabled = True
        self.allow_read = True
        self.allow_create = True
        self.allow_write = True
        self.allow_move = True
        self.allow_copy = True
        self.allow_delete = False
        self.allowed_roots_raw = ["./", "~/Documents", "~/Downloads", "~/Desktop"]
        self.protected_roots_raw = []
        self.sensitive_patterns = []

        self._load_config()
        self.path_resolver = PathResolver(self.allowed_roots_raw)
        self.sensitivity_checker = SensitivityChecker(
            sensitive_patterns=self.sensitive_patterns,
            protected_roots=self.protected_roots_raw,
        )

    def _load_config(self) -> None:
        if self.config_path.exists():
            with open(self.config_path, "r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f) or {}
                fs_cfg = cfg.get("filesystem", {})
                self.enabled = fs_cfg.get("enabled", True)
                self.allow_read = fs_cfg.get("allow_read", True)
                self.allow_create = fs_cfg.get("allow_create", True)
                self.allow_write = fs_cfg.get("allow_write", True)
                self.allow_move = fs_cfg.get("allow_move", True)
                self.allow_copy = fs_cfg.get("allow_copy", True)
                self.allow_delete = fs_cfg.get("allow_delete", False)
                self.allowed_roots_raw = fs_cfg.get("allowed_roots", self.allowed_roots_raw)
                self.protected_roots_raw = fs_cfg.get("protected_roots", [])
                self.sensitive_patterns = fs_cfg.get("sensitive_patterns", [])

    def evaluate_operation(
        self,
        operation: str,
        target_path: Optional[Union[str, Path]] = None,
        destination_path: Optional[Union[str, Path]] = None,
        bulk: bool = False,
    ) -> RiskLevel:
        """
        Evaluates permission for a filesystem operation.
        Raises FilesystemUnavailable or PermissionDenied if violated.
        Returns the assessed RiskLevel.
        """
        if not self.enabled:
            raise FilesystemUnavailable("Filesystem subsystem is disabled in configuration.")

        # Check operation flags
        if operation in ("list_directory", "read_file", "search_files", "get_metadata", "find_duplicates", "get_storage_info"):
            if not self.allow_read:
                raise PermissionDenied(f"Read operations are disabled by policy.")
            category = PermissionCategory.READ_FILES
            risk = RiskLevel.LOW

        elif operation in ("create_file", "create_directory"):
            if not self.allow_create:
                raise PermissionDenied(f"File/Directory creation is disabled by policy.")
            category = PermissionCategory.WRITE_FILES
            risk = RiskLevel.MEDIUM

        elif operation in ("write_file", "edit_file"):
            if not self.allow_write:
                raise PermissionDenied(f"File writing/editing is disabled by policy.")
            category = PermissionCategory.WRITE_FILES
            risk = RiskLevel.HIGH if bulk else RiskLevel.MEDIUM

        elif operation in ("copy_file", "move_file", "rename_file", "organize"):
            if operation == "copy_file" and not self.allow_copy:
                raise PermissionDenied(f"File copying is disabled by policy.")
            if operation in ("move_file", "rename_file", "organize") and not self.allow_move:
                raise PermissionDenied(f"File move/rename is disabled by policy.")
            category = PermissionCategory.WRITE_FILES
            risk = RiskLevel.HIGH if bulk else RiskLevel.MEDIUM

        elif operation in ("delete_file", "delete_directory"):
            if not self.allow_delete:
                raise PermissionDenied(
                    f"File/Directory deletion is currently disabled in config (allow_delete=false)."
                )
            category = PermissionCategory.DELETE_FILES
            risk = RiskLevel.CRITICAL if (bulk or operation == "delete_directory") else RiskLevel.HIGH
        else:
            category = PermissionCategory.WRITE_FILES
            risk = RiskLevel.HIGH

        # Validate target path security
        if target_path:
            resolved_target = self.path_resolver.resolve_path(target_path, check_allowed=True)
            self.sensitivity_checker.check_safety(resolved_target)

        # Validate destination path security
        if destination_path:
            resolved_dest = self.path_resolver.resolve_path(destination_path, check_allowed=True)
            self.sensitivity_checker.check_safety(resolved_dest)

        # Evaluate against central security evaluator
        sec_result = self.security_evaluator.evaluate(
            category=category,
            risk_level=risk,
            action_name=f"filesystem.{operation}",
            parameters={"target": str(target_path), "dest": str(destination_path)},
        )

        if not sec_result.allowed:
            raise PermissionDenied(sec_result.reason)

        return risk
