"""
Central Filesystem Manager orchestrating all filesystem operations in JARVIS.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel

from jarvis.filesystem.duplicates import DuplicateFinder, DuplicateReport
from jarvis.filesystem.editor import EditOperationResult, FileEditor
from jarvis.filesystem.errors import FilesystemError, PathNotFound, PermissionDenied
from jarvis.filesystem.metadata import FileMetadata, MetadataExtractor
from jarvis.filesystem.operations import FileOperations, RollbackRecord
from jarvis.filesystem.organization import FileOrganizer, OrganizationExecutionReport, OrganizationPlan
from jarvis.filesystem.paths import PathResolver
from jarvis.filesystem.permissions import FilesystemPermissionChecker
from jarvis.filesystem.reader import FileReader, ReadFileResult
from jarvis.filesystem.search import FileSearchEngine, SearchQuery, SearchResult
from jarvis.filesystem.storage import StorageInfo, StorageInfoProvider
from jarvis.filesystem.writer import FileWriter, WriteFileResult


class DirectoryListResult(BaseModel):
    path: str
    total_entries: int
    entries: List[FileMetadata]
    truncated: bool


class FilesystemManager:
    """Central entrypoint for safe, verified filesystem operations."""

    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        self.permission_checker = FilesystemPermissionChecker(config_path=config_path)
        self.path_resolver = self.permission_checker.path_resolver
        self.reader = FileReader()
        self.editor = FileEditor()
        self.search_engine = FileSearchEngine(reader=self.reader)
        self.duplicate_finder = DuplicateFinder()
        self.storage_provider = StorageInfoProvider()
        self.operations = FileOperations()
        self.organizer = FileOrganizer(file_operations=self.operations)

    def list_directory(
        self,
        path: Union[str, Path],
        recursive: bool = False,
        limit: int = 200,
        max_depth: int = 2,
    ) -> DirectoryListResult:
        """Lists directory entries with pagination and bounds."""
        self.permission_checker.evaluate_operation("list_directory", target_path=path)
        resolved = self.path_resolver.resolve_path(path, check_allowed=True)

        if not resolved.exists():
            raise PathNotFound(f"Directory '{resolved}' does not exist.")
        if not resolved.is_dir():
            raise ValueError(f"Path '{resolved}' is a file, not a directory.")

        entries: List[FileMetadata] = []
        truncated = False
        count = 0

        if not recursive:
            for child in resolved.iterdir():
                try:
                    meta = MetadataExtractor.get_metadata(child, calculate_hash=False)
                    entries.append(meta)
                    count += 1
                    if count >= limit:
                        truncated = True
                        break
                except Exception:
                    continue
        else:
            q = SearchQuery(
                root_path=str(resolved),
                max_results=limit,
                max_depth=max_depth,
            )
            s_res = self.search_engine.search(q)
            entries = s_res.results
            truncated = s_res.truncated

        return DirectoryListResult(
            path=str(resolved),
            total_entries=len(entries),
            entries=entries,
            truncated=truncated,
        )

    def read_file(
        self,
        path: Union[str, Path],
        start_line: Optional[int] = None,
        end_line: Optional[int] = None,
        max_bytes: Optional[int] = None,
    ) -> ReadFileResult:
        """Reads text file contents safely."""
        self.permission_checker.evaluate_operation("read_file", target_path=path)
        resolved = self.path_resolver.resolve_path(path, check_allowed=True)
        return self.reader.read_text_file(
            resolved,
            start_line=start_line,
            end_line=end_line,
            max_bytes=max_bytes,
        )

    def create_file(
        self,
        path: Union[str, Path],
        content: str = "",
        overwrite: bool = False,
    ) -> WriteFileResult:
        """Creates a new file with content."""
        self.permission_checker.evaluate_operation("create_file", target_path=path)
        resolved = self.path_resolver.resolve_path(path, check_allowed=True)
        return FileWriter.write_file(resolved, content, overwrite=overwrite, atomic=True)

    def write_file(
        self,
        path: Union[str, Path],
        content: str,
        overwrite: bool = False,
    ) -> WriteFileResult:
        """Writes content to file."""
        self.permission_checker.evaluate_operation("write_file", target_path=path)
        resolved = self.path_resolver.resolve_path(path, check_allowed=True)
        return FileWriter.write_file(resolved, content, overwrite=overwrite, atomic=True)

    def edit_file(
        self,
        path: Union[str, Path],
        operation: str,
        target_text: Optional[str] = None,
        replacement_text: Optional[str] = None,
        line_number: Optional[int] = None,
        json_key: Optional[str] = None,
        json_value: Optional[Any] = None,
        create_backup: bool = True,
    ) -> EditOperationResult:
        """Edits target file content."""
        self.permission_checker.evaluate_operation("edit_file", target_path=path)
        resolved = self.path_resolver.resolve_path(path, check_allowed=True)
        return self.editor.edit_file(
            target_path=resolved,
            operation=operation,
            target_text=target_text,
            replacement_text=replacement_text,
            line_number=line_number,
            json_key=json_key,
            json_value=json_value,
            create_backup_file=create_backup,
        )

    def copy_file(
        self,
        source: Union[str, Path],
        destination: Union[str, Path],
        overwrite: bool = False,
    ) -> RollbackRecord:
        """Copies file to destination."""
        self.permission_checker.evaluate_operation("copy_file", target_path=source, destination_path=destination)
        res_src = self.path_resolver.resolve_path(source, check_allowed=True)
        res_dst = self.path_resolver.resolve_path(destination, check_allowed=True)
        return self.operations.copy_file(res_src, res_dst, overwrite=overwrite)

    def move_file(
        self,
        source: Union[str, Path],
        destination: Union[str, Path],
        overwrite: bool = False,
    ) -> RollbackRecord:
        """Moves file to destination."""
        self.permission_checker.evaluate_operation("move_file", target_path=source, destination_path=destination)
        res_src = self.path_resolver.resolve_path(source, check_allowed=True)
        res_dst = self.path_resolver.resolve_path(destination, check_allowed=True)
        return self.operations.move_file(res_src, res_dst, overwrite=overwrite)

    def rename_file(
        self,
        path: Union[str, Path],
        new_name: str,
    ) -> RollbackRecord:
        """Renames file or folder."""
        self.permission_checker.evaluate_operation("rename_file", target_path=path)
        res_target = self.path_resolver.resolve_path(path, check_allowed=True)
        return self.operations.rename_file(res_target, new_name)

    def create_directory(
        self,
        path: Union[str, Path],
        exist_ok: bool = True,
    ) -> RollbackRecord:
        """Creates directory."""
        self.permission_checker.evaluate_operation("create_directory", target_path=path)
        res_target = self.path_resolver.resolve_path(path, check_allowed=True)
        return self.operations.create_directory(res_target, exist_ok=exist_ok)

    def delete_file(
        self,
        path: Union[str, Path],
    ) -> RollbackRecord:
        """Deletes file."""
        self.permission_checker.evaluate_operation("delete_file", target_path=path)
        res_target = self.path_resolver.resolve_path(path, check_allowed=True)
        return self.operations.delete_file(res_target)

    def delete_directory(
        self,
        path: Union[str, Path],
        recursive: bool = False,
    ) -> RollbackRecord:
        """Deletes directory."""
        self.permission_checker.evaluate_operation("delete_directory", target_path=path, bulk=recursive)
        res_target = self.path_resolver.resolve_path(path, check_allowed=True)
        return self.operations.delete_directory(res_target, recursive=recursive)

    def get_metadata(
        self,
        path: Union[str, Path],
        calculate_hash: bool = False,
    ) -> FileMetadata:
        """Retrieves metadata."""
        self.permission_checker.evaluate_operation("get_metadata", target_path=path)
        res_target = self.path_resolver.resolve_path(path, check_allowed=True)
        return MetadataExtractor.get_metadata(res_target, calculate_hash=calculate_hash)

    def search_files(
        self,
        root_path: Union[str, Path],
        pattern: Optional[str] = None,
        extension: Optional[str] = None,
        text_content: Optional[str] = None,
        max_results: int = 100,
        max_depth: int = 10,
    ) -> SearchResult:
        """Searches files under root_path."""
        self.permission_checker.evaluate_operation("search_files", target_path=root_path)
        res_target = self.path_resolver.resolve_path(root_path, check_allowed=True)
        q = SearchQuery(
            root_path=str(res_target),
            pattern=pattern,
            extension=extension,
            text_content=text_content,
            max_results=max_results,
            max_depth=max_depth,
        )
        return self.search_engine.search(q)

    def find_duplicates(
        self,
        root_path: Union[str, Path],
    ) -> DuplicateReport:
        """Scans for duplicate files under root_path."""
        self.permission_checker.evaluate_operation("find_duplicates", target_path=root_path)
        res_target = self.path_resolver.resolve_path(root_path, check_allowed=True)
        return self.duplicate_finder.find_duplicates(res_target)

    def get_storage_info(
        self,
        path: Optional[Union[str, Path]] = None,
    ) -> StorageInfo:
        """Gets storage info for path or current volume."""
        self.permission_checker.evaluate_operation("get_storage_info", target_path=path)
        res_target = self.path_resolver.resolve_path(path, check_allowed=True) if path else None
        return self.storage_provider.get_storage_info(res_target)

    def organize_directory(
        self,
        target_directory: Union[str, Path],
        execute: bool = False,
    ) -> Union[OrganizationPlan, OrganizationExecutionReport]:
        """Generates or executes a file organization plan."""
        self.permission_checker.evaluate_operation("organize", target_path=target_directory, bulk=True)
        res_target = self.path_resolver.resolve_path(target_directory, check_allowed=True)
        plan = self.organizer.generate_plan(res_target)
        if not execute:
            return plan
        return self.organizer.execute_plan(plan)
