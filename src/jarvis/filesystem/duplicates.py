"""
Efficient 3-stage duplicate file detection module for JARVIS.
"""

import hashlib
import os
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseModel

from jarvis.filesystem.metadata import MetadataExtractor


class DuplicateGroup(BaseModel):
    sha256: str
    size_bytes: int
    count: int
    files: List[str]


class DuplicateReport(BaseModel):
    root_path: str
    total_files_scanned: int
    duplicate_groups_found: int
    potential_savings_bytes: int
    groups: List[DuplicateGroup]


class DuplicateFinder:
    """Staged comparison duplicate detection (Size -> 4KB Partial Hash -> Full SHA-256)."""

    @staticmethod
    def compute_partial_hash(path: Path, chunk_size: int = 4096) -> str:
        """Computes hash of the first chunk of a file."""
        hasher = hashlib.md5()
        with open(path, "rb") as f:
            chunk = f.read(chunk_size)
            hasher.update(chunk)
        return hasher.hexdigest()

    def find_duplicates(
        self,
        root_path: Path,
        max_files_scanned: int = 10000,
        min_file_size: int = 1024,  # Ignore files smaller than 1KB
    ) -> DuplicateReport:
        """Finds duplicate files using staged multi-pass filtering."""
        root = root_path.resolve(strict=False)
        if not root.exists():
            return DuplicateReport(
                root_path=str(root),
                total_files_scanned=0,
                duplicate_groups_found=0,
                potential_savings_bytes=0,
                groups=[],
            )

        # Pass 1: Size grouping
        size_groups: Dict[int, List[Path]] = defaultdict(list)
        total_scanned = 0

        for dirpath, dirnames, filenames in os.walk(root):
            # Exclude hidden / venv directories
            dirnames[:] = [d for d in dirnames if not d.startswith(".") and d not in {"node_modules", "__pycache__", "venv"}]

            for fname in filenames:
                total_scanned += 1
                if total_scanned > max_files_scanned:
                    break

                fpath = Path(dirpath) / fname
                try:
                    st = fpath.stat(follow_symlinks=False)
                    if st.st_size >= min_file_size:
                        size_groups[st.st_size].append(fpath)
                except Exception:
                    continue

            if total_scanned > max_files_scanned:
                break

        # Pass 2: Filter candidate size groups with > 1 file, then compute partial hash
        partial_hash_groups: Dict[tuple, List[Path]] = defaultdict(list)
        for size, file_list in size_groups.items():
            if len(file_list) > 1:
                for fpath in file_list:
                    try:
                        p_hash = self.compute_partial_hash(fpath)
                        partial_hash_groups[(size, p_hash)].append(fpath)
                    except Exception:
                        continue

        # Pass 3: Compute full SHA-256 for partial match candidate groups
        final_groups: List[DuplicateGroup] = []
        potential_savings = 0

        for (size, p_hash), file_list in partial_hash_groups.items():
            if len(file_list) > 1:
                full_hash_groups: Dict[str, List[Path]] = defaultdict(list)
                for fpath in file_list:
                    try:
                        full_h = MetadataExtractor.compute_sha256(fpath)
                        full_hash_groups[full_h].append(fpath)
                    except Exception:
                        continue

                for full_h, dups in full_hash_groups.items():
                    if len(dups) > 1:
                        dup_strs = [str(p.resolve(strict=False)) for p in dups]
                        final_groups.append(
                            DuplicateGroup(
                                sha256=full_h,
                                size_bytes=size,
                                count=len(dups),
                                files=dup_strs,
                            )
                        )
                        potential_savings += size * (len(dups) - 1)

        return DuplicateReport(
            root_path=str(root),
            total_files_scanned=total_scanned,
            duplicate_groups_found=len(final_groups),
            potential_savings_bytes=potential_savings,
            groups=final_groups,
        )
