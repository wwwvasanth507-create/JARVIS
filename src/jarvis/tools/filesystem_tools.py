"""
Structured Filesystem Tools for JARVIS Tool Subsystem.
"""

from typing import Any, Dict, Optional
from jarvis.filesystem.manager import FilesystemManager
from jarvis.security.permissions import PermissionCategory, RiskLevel
from jarvis.tools.base import BaseTool, ToolMetadata, ToolResult


# Global manager instance
_fs_manager = FilesystemManager()


class ListDirectoryTool(BaseTool):
    def __init__(self, manager: Optional[FilesystemManager] = None):
        self.mgr = manager or _fs_manager
        super().__init__(
            ToolMetadata(
                name="filesystem.list_directory",
                description="List contents of a directory with bounds and metadata.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Target directory path"},
                        "recursive": {"type": "boolean", "default": False},
                        "limit": {"type": "integer", "default": 200},
                    },
                    "required": ["path"],
                },
                permission_requirement=PermissionCategory.READ_FILES,
                risk_level=RiskLevel.LOW,
                verification_strategy="directory_listed",
            )
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        try:
            res = self.mgr.list_directory(
                path=kwargs["path"],
                recursive=kwargs.get("recursive", False),
                limit=kwargs.get("limit", 200),
            )
            return ToolResult(success=True, data=res.model_dump())
        except Exception as e:
            return self.handle_error(e)

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class ReadFileTool(BaseTool):
    def __init__(self, manager: Optional[FilesystemManager] = None):
        self.mgr = manager or _fs_manager
        super().__init__(
            ToolMetadata(
                name="filesystem.read_file",
                description="Read contents of a text file with encoding detection and bounds.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Target file path"},
                        "start_line": {"type": "integer"},
                        "end_line": {"type": "integer"},
                        "max_bytes": {"type": "integer"},
                    },
                    "required": ["path"],
                },
                permission_requirement=PermissionCategory.READ_FILES,
                risk_level=RiskLevel.LOW,
                verification_strategy="content_read",
            )
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        try:
            res = self.mgr.read_file(
                path=kwargs["path"],
                start_line=kwargs.get("start_line"),
                end_line=kwargs.get("end_line"),
                max_bytes=kwargs.get("max_bytes"),
            )
            return ToolResult(success=True, data=res.model_dump())
        except Exception as e:
            return self.handle_error(e)

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class CreateFileTool(BaseTool):
    def __init__(self, manager: Optional[FilesystemManager] = None):
        self.mgr = manager or _fs_manager
        super().__init__(
            ToolMetadata(
                name="filesystem.create_file",
                description="Create a new file with optional content.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Target file path"},
                        "content": {"type": "string", "default": ""},
                        "overwrite": {"type": "boolean", "default": False},
                    },
                    "required": ["path"],
                },
                permission_requirement=PermissionCategory.WRITE_FILES,
                risk_level=RiskLevel.MEDIUM,
                verification_strategy="file_created",
            )
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        try:
            res = self.mgr.create_file(
                path=kwargs["path"],
                content=kwargs.get("content", ""),
                overwrite=kwargs.get("overwrite", False),
            )
            return ToolResult(success=True, data=res.model_dump())
        except Exception as e:
            return self.handle_error(e)

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class WriteFileTool(BaseTool):
    def __init__(self, manager: Optional[FilesystemManager] = None):
        self.mgr = manager or _fs_manager
        super().__init__(
            ToolMetadata(
                name="filesystem.write_file",
                description="Write content to a file atomically.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Target file path"},
                        "content": {"type": "string"},
                        "overwrite": {"type": "boolean", "default": False},
                    },
                    "required": ["path", "content"],
                },
                permission_requirement=PermissionCategory.WRITE_FILES,
                risk_level=RiskLevel.MEDIUM,
                verification_strategy="atomic_write",
            )
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        try:
            res = self.mgr.write_file(
                path=kwargs["path"],
                content=kwargs["content"],
                overwrite=kwargs.get("overwrite", False),
            )
            return ToolResult(success=True, data=res.model_dump())
        except Exception as e:
            return self.handle_error(e)

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class EditFileTool(BaseTool):
    def __init__(self, manager: Optional[FilesystemManager] = None):
        self.mgr = manager or _fs_manager
        super().__init__(
            ToolMetadata(
                name="filesystem.edit_file",
                description="Perform controlled targeted edits on a text/JSON file.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                        "operation": {
                            "type": "string",
                            "enum": ["replace_exact", "insert_line", "append_text", "edit_json_key"],
                        },
                        "target_text": {"type": "string"},
                        "replacement_text": {"type": "string"},
                        "line_number": {"type": "integer"},
                        "json_key": {"type": "string"},
                        "json_value": {},
                        "create_backup": {"type": "boolean", "default": True},
                    },
                    "required": ["path", "operation"],
                },
                permission_requirement=PermissionCategory.WRITE_FILES,
                risk_level=RiskLevel.MEDIUM,
                verification_strategy="hash_verification",
            )
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        try:
            res = self.mgr.edit_file(
                path=kwargs["path"],
                operation=kwargs["operation"],
                target_text=kwargs.get("target_text"),
                replacement_text=kwargs.get("replacement_text"),
                line_number=kwargs.get("line_number"),
                json_key=kwargs.get("json_key"),
                json_value=kwargs.get("json_value"),
                create_backup=kwargs.get("create_backup", True),
            )
            return ToolResult(success=True, data=res.model_dump())
        except Exception as e:
            return self.handle_error(e)

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class CopyFileTool(BaseTool):
    def __init__(self, manager: Optional[FilesystemManager] = None):
        self.mgr = manager or _fs_manager
        super().__init__(
            ToolMetadata(
                name="filesystem.copy",
                description="Copy a file to destination path.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "source": {"type": "string"},
                        "destination": {"type": "string"},
                        "overwrite": {"type": "boolean", "default": False},
                    },
                    "required": ["source", "destination"],
                },
                permission_requirement=PermissionCategory.WRITE_FILES,
                risk_level=RiskLevel.MEDIUM,
                verification_strategy="copy_verified",
            )
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        try:
            res = self.mgr.copy_file(
                source=kwargs["source"],
                destination=kwargs["destination"],
                overwrite=kwargs.get("overwrite", False),
            )
            return ToolResult(success=True, data=res.model_dump())
        except Exception as e:
            return self.handle_error(e)

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class MoveFileTool(BaseTool):
    def __init__(self, manager: Optional[FilesystemManager] = None):
        self.mgr = manager or _fs_manager
        super().__init__(
            ToolMetadata(
                name="filesystem.move",
                description="Move a file or folder to destination path.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "source": {"type": "string"},
                        "destination": {"type": "string"},
                        "overwrite": {"type": "boolean", "default": False},
                    },
                    "required": ["source", "destination"],
                },
                permission_requirement=PermissionCategory.WRITE_FILES,
                risk_level=RiskLevel.MEDIUM,
                verification_strategy="move_verified",
            )
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        try:
            res = self.mgr.move_file(
                source=kwargs["source"],
                destination=kwargs["destination"],
                overwrite=kwargs.get("overwrite", False),
            )
            return ToolResult(success=True, data=res.model_dump())
        except Exception as e:
            return self.handle_error(e)

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class RenameFileTool(BaseTool):
    def __init__(self, manager: Optional[FilesystemManager] = None):
        self.mgr = manager or _fs_manager
        super().__init__(
            ToolMetadata(
                name="filesystem.rename",
                description="Rename a file or folder.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                        "new_name": {"type": "string"},
                    },
                    "required": ["path", "new_name"],
                },
                permission_requirement=PermissionCategory.WRITE_FILES,
                risk_level=RiskLevel.MEDIUM,
                verification_strategy="rename_verified",
            )
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        try:
            res = self.mgr.rename_file(
                path=kwargs["path"],
                new_name=kwargs["new_name"],
            )
            return ToolResult(success=True, data=res.model_dump())
        except Exception as e:
            return self.handle_error(e)

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class CreateDirectoryTool(BaseTool):
    def __init__(self, manager: Optional[FilesystemManager] = None):
        self.mgr = manager or _fs_manager
        super().__init__(
            ToolMetadata(
                name="filesystem.create_directory",
                description="Create a new directory structure.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                        "exist_ok": {"type": "boolean", "default": True},
                    },
                    "required": ["path"],
                },
                permission_requirement=PermissionCategory.WRITE_FILES,
                risk_level=RiskLevel.MEDIUM,
                verification_strategy="directory_created",
            )
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        try:
            res = self.mgr.create_directory(
                path=kwargs["path"],
                exist_ok=kwargs.get("exist_ok", True),
            )
            return ToolResult(success=True, data=res.model_dump())
        except Exception as e:
            return self.handle_error(e)

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class DeleteFileTool(BaseTool):
    def __init__(self, manager: Optional[FilesystemManager] = None):
        self.mgr = manager or _fs_manager
        super().__init__(
            ToolMetadata(
                name="filesystem.delete_file",
                description="Delete a file safely.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                    },
                    "required": ["path"],
                },
                permission_requirement=PermissionCategory.DELETE_FILES,
                risk_level=RiskLevel.HIGH,
                verification_strategy="deletion_verified",
            )
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        try:
            res = self.mgr.delete_file(path=kwargs["path"])
            return ToolResult(success=True, data=res.model_dump())
        except Exception as e:
            return self.handle_error(e)

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class DeleteDirectoryTool(BaseTool):
    def __init__(self, manager: Optional[FilesystemManager] = None):
        self.mgr = manager or _fs_manager
        super().__init__(
            ToolMetadata(
                name="filesystem.delete_directory",
                description="Delete a directory structure.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                        "recursive": {"type": "boolean", "default": False},
                    },
                    "required": ["path"],
                },
                permission_requirement=PermissionCategory.DELETE_FILES,
                risk_level=RiskLevel.CRITICAL,
                verification_strategy="directory_deletion_verified",
            )
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        try:
            res = self.mgr.delete_directory(
                path=kwargs["path"],
                recursive=kwargs.get("recursive", False),
            )
            return ToolResult(success=True, data=res.model_dump())
        except Exception as e:
            return self.handle_error(e)

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class SearchFilesTool(BaseTool):
    def __init__(self, manager: Optional[FilesystemManager] = None):
        self.mgr = manager or _fs_manager
        super().__init__(
            ToolMetadata(
                name="filesystem.search",
                description="Search files by pattern, extension, size, date, or content.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "root_path": {"type": "string"},
                        "pattern": {"type": "string"},
                        "extension": {"type": "string"},
                        "text_content": {"type": "string"},
                        "max_results": {"type": "integer", "default": 100},
                        "max_depth": {"type": "integer", "default": 10},
                    },
                    "required": ["root_path"],
                },
                permission_requirement=PermissionCategory.READ_FILES,
                risk_level=RiskLevel.LOW,
                verification_strategy="search_completed",
            )
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        try:
            res = self.mgr.search_files(
                root_path=kwargs["root_path"],
                pattern=kwargs.get("pattern"),
                extension=kwargs.get("extension"),
                text_content=kwargs.get("text_content"),
                max_results=kwargs.get("max_results", 100),
                max_depth=kwargs.get("max_depth", 10),
            )
            return ToolResult(success=True, data=res.model_dump())
        except Exception as e:
            return self.handle_error(e)

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class GetMetadataTool(BaseTool):
    def __init__(self, manager: Optional[FilesystemManager] = None):
        self.mgr = manager or _fs_manager
        super().__init__(
            ToolMetadata(
                name="filesystem.metadata",
                description="Get detailed metadata and file attributes for a path.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                        "calculate_hash": {"type": "boolean", "default": False},
                    },
                    "required": ["path"],
                },
                permission_requirement=PermissionCategory.READ_FILES,
                risk_level=RiskLevel.LOW,
                verification_strategy="metadata_read",
            )
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        try:
            res = self.mgr.get_metadata(
                path=kwargs["path"],
                calculate_hash=kwargs.get("calculate_hash", False),
            )
            return ToolResult(success=True, data=res.model_dump())
        except Exception as e:
            return self.handle_error(e)

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class FindDuplicatesTool(BaseTool):
    def __init__(self, manager: Optional[FilesystemManager] = None):
        self.mgr = manager or _fs_manager
        super().__init__(
            ToolMetadata(
                name="filesystem.find_duplicates",
                description="Scan for duplicate files under a root directory.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "root_path": {"type": "string"},
                    },
                    "required": ["root_path"],
                },
                permission_requirement=PermissionCategory.READ_FILES,
                risk_level=RiskLevel.LOW,
                verification_strategy="duplicates_scanned",
            )
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        try:
            res = self.mgr.find_duplicates(root_path=kwargs["root_path"])
            return ToolResult(success=True, data=res.model_dump())
        except Exception as e:
            return self.handle_error(e)

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class GetStorageInfoTool(BaseTool):
    def __init__(self, manager: Optional[FilesystemManager] = None):
        self.mgr = manager or _fs_manager
        super().__init__(
            ToolMetadata(
                name="filesystem.storage_info",
                description="Report storage and disk space utilization.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                    },
                },
                permission_requirement=PermissionCategory.READ_FILES,
                risk_level=RiskLevel.LOW,
                verification_strategy="storage_read",
            )
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        try:
            res = self.mgr.get_storage_info(path=kwargs.get("path"))
            return ToolResult(success=True, data=res.model_dump())
        except Exception as e:
            return self.handle_error(e)

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class OrganizeDirectoryTool(BaseTool):
    def __init__(self, manager: Optional[FilesystemManager] = None):
        self.mgr = manager or _fs_manager
        super().__init__(
            ToolMetadata(
                name="filesystem.organize",
                description="Generate or execute a file organization plan for a directory.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "target_directory": {"type": "string"},
                        "execute": {"type": "boolean", "default": False},
                    },
                    "required": ["target_directory"],
                },
                permission_requirement=PermissionCategory.WRITE_FILES,
                risk_level=RiskLevel.HIGH,
                verification_strategy="plan_or_execution_verified",
            )
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        try:
            res = self.mgr.organize_directory(
                target_directory=kwargs["target_directory"],
                execute=kwargs.get("execute", False),
            )
            return ToolResult(success=True, data=res.model_dump())
        except Exception as e:
            return self.handle_error(e)

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


FILESYSTEM_TOOLS = [
    ListDirectoryTool(),
    ReadFileTool(),
    CreateFileTool(),
    WriteFileTool(),
    EditFileTool(),
    CopyFileTool(),
    MoveFileTool(),
    RenameFileTool(),
    CreateDirectoryTool(),
    DeleteFileTool(),
    DeleteDirectoryTool(),
    SearchFilesTool(),
    GetMetadataTool(),
    FindDuplicatesTool(),
    GetStorageInfoTool(),
    OrganizeDirectoryTool(),
]
