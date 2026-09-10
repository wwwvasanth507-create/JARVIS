"""
File and content search engine for JARVIS.
"""

import fnmatch
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union
from pydantic import BaseModel

from jarvis.filesystem.metadata import MetadataExtractor, FileMetadata
from jarvis.filesystem.reader import FileReader


DEFAULT_EXCLUSIONS = {
    ".git", ".svn", ".hg", "__pycache__", "node_modules",
    ".venv", "venv", ".idea", ".vscode", "dist", "build",
}


class SearchQuery(BaseModel):
    root_path: str
    pattern: Optional[str] = None
    extension: Optional[str] = None
    text_content: Optional[str] = None
    min_size_bytes: Optional[int] = None
    max_size_bytes: Optional[int] = None
    modified_after: Optional[str] = None
    modified_before: Optional[str] = None
    max_results: int = 100
    max_depth: int = 10


class SearchResult(BaseModel):
    query: SearchQuery
    results: List[FileMetadata]
    total_found: int
    truncated: bool
    scan_duration_ms: float


class FileSearchEngine:
    """Fast, resource-capped file search engine with exclusions and content matching."""

    def __init__(self, reader: Optional[FileReader] = None):
        self.reader = reader or FileReader()

    def search(
        self,
        query: SearchQuery,
        cancel_event: Optional[threading.Event] = None,
        progress_callback: Optional[Callable[[int], None]] = None,
    ) -> SearchResult:
        """Executes a multi-criteria search under query.root_path."""
        start_time = datetime.now(timezone.utc)
        root = Path(query.root_path).resolve(strict=False)

        if not root.exists():
            return SearchResult(
                query=query,
                results=[],
                total_found=0,
                truncated=False,
                scan_duration_ms=0.0,
            )

        # Parse date filters
        mod_after_dt = None
        if query.modified_after:
            try:
                mod_after_dt = datetime.fromisoformat(query.modified_after)
            except Exception:
                pass

        mod_before_dt = None
        if query.modified_before:
            try:
                mod_before_dt = datetime.fromisoformat(query.modified_before)
            except Exception:
                pass

        matched_files: List[FileMetadata] = []
        total_found = 0
        truncated = False
        scanned_count = 0

        target_ext = query.extension.lower() if query.extension else None
        if target_ext and not target_ext.startswith("."):
            target_ext = f".{target_ext}"

        for dirpath, dirnames, filenames in os.walk(root, topdown=True):
            if cancel_event and cancel_event.is_set():
                break

            # Prune excluded directories
            dirnames[:] = [d for d in dirnames if d not in DEFAULT_EXCLUSIONS]

            # Depth restriction
            current_path = Path(dirpath)
            try:
                rel = current_path.relative_to(root)
                depth = len(rel.parts)
            except ValueError:
                depth = 0

            if depth > query.max_depth:
                dirnames.clear()
                continue

            for fname in filenames:
                if cancel_event and cancel_event.is_set():
                    break

                scanned_count += 1
                if progress_callback and scanned_count % 100 == 0:
                    progress_callback(scanned_count)

                fpath = current_path / fname

                # 1. Pattern filter
                if query.pattern and not fnmatch.fnmatch(fname.lower(), query.pattern.lower()):
                    continue

                # 2. Extension filter
                if target_ext and fpath.suffix.lower() != target_ext:
                    continue

                try:
                    st = fpath.stat()
                except Exception:
                    continue

                # 3. Size filter
                if query.min_size_bytes is not None and st.st_size < query.min_size_bytes:
                    continue
                if query.max_size_bytes is not None and st.st_size > query.max_size_bytes:
                    continue

                # 4. Date filter
                mtime_dt = datetime.fromtimestamp(st.st_mtime, tz=timezone.utc)
                if mod_after_dt and mtime_dt < mod_after_dt:
                    continue
                if mod_before_dt and mtime_dt > mod_before_dt:
                    continue

                # 5. Content search filter
                if query.text_content:
                    try:
                        read_res = self.reader.read_text_file(fpath, max_bytes=524288)
                        if query.text_content.lower() not in read_res.content.lower():
                            continue
                    except Exception:
                        continue

                total_found += 1
                if len(matched_files) < query.max_results:
                    try:
                        meta = MetadataExtractor.get_metadata(fpath, calculate_hash=False)
                        matched_files.append(meta)
                    except Exception:
                        pass
                else:
                    truncated = True

        duration = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000.0

        return SearchResult(
            query=query,
            results=matched_files,
            total_found=total_found,
            truncated=truncated,
            scan_duration_ms=duration,
        )
