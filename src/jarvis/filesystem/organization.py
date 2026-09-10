"""
File organization subsystem for JARVIS (Inspect -> Categorize -> Plan -> Confirm -> Execute -> Verify).
"""

from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseModel

from jarvis.filesystem.metadata import MetadataExtractor, FILE_TYPE_EXTENSIONS
from jarvis.filesystem.operations import FileOperations


class MoveItem(BaseModel):
    source: str
    destination: str
    category: str


class OrganizationPlan(BaseModel):
    target_directory: str
    moves: List[MoveItem]
    category_counts: Dict[str, int]
    total_files_to_move: int
    requires_boss_approval: bool


class OrganizationExecutionReport(BaseModel):
    target_directory: str
    total_files_processed: int
    successful_moves: int
    failed_moves: int
    details: List[Dict[str, str]]


CATEGORY_SUBDIRECTORIES = {
    "PDF": "Documents/PDFs",
    "Text": "Documents/TextFiles",
    "Markdown": "Documents/Notes",
    "JSON": "Documents/Data",
    "YAML": "Documents/Data",
    "CSV": "Documents/Data",
    "Code": "Development/Code",
    "Image": "Pictures",
    "Audio": "Music",
    "Video": "Videos",
    "Archive": "Archives",
    "Executable": "Applications",
}


class FileOrganizer:
    """Provides plan-first bulk file organization workflows."""

    def __init__(self, file_operations: Optional[FileOperations] = None):
        self.ops = file_operations or FileOperations()

    def generate_plan(
        self,
        target_directory: Path,
        destination_root: Optional[Path] = None,
    ) -> OrganizationPlan:
        """
        Scans target_directory and builds a proposed organization plan
        without moving any files.
        """
        root = target_directory.resolve(strict=False)
        dest_base = (destination_root or root).resolve(strict=False)

        moves: List[MoveItem] = []
        category_counts: Dict[str, int] = {}

        if not root.exists() or not root.is_dir():
            return OrganizationPlan(
                target_directory=str(root),
                moves=[],
                category_counts={},
                total_files_to_move=0,
                requires_boss_approval=False,
            )

        for child in root.iterdir():
            if child.is_file() and not child.name.startswith("."):
                file_type = MetadataExtractor.identify_file_type(child)
                if file_type == "Unknown":
                    continue

                sub_dir = CATEGORY_SUBDIRECTORIES.get(file_type, f"Organized/{file_type}")
                target_dest_folder = dest_base / sub_dir
                target_dest_file = target_dest_folder / child.name

                moves.append(
                    MoveItem(
                        source=str(child.resolve(strict=False)),
                        destination=str(target_dest_file.resolve(strict=False)),
                        category=file_type,
                    )
                )
                category_counts[file_type] = category_counts.get(file_type, 0) + 1

        requires_approval = len(moves) > 5  # Require approval for > 5 moves

        return OrganizationPlan(
            target_directory=str(root),
            moves=moves,
            category_counts=category_counts,
            total_files_to_move=len(moves),
            requires_boss_approval=requires_approval,
        )

    def execute_plan(self, plan: OrganizationPlan) -> OrganizationExecutionReport:
        """Executes an approved organization plan and verifies individual moves."""
        successful = 0
        failed = 0
        details: List[Dict[str, str]] = []

        for item in plan.moves:
            src = Path(item.source)
            dst = Path(item.destination)
            try:
                self.ops.move_file(src, dst, overwrite=False)
                successful += 1
                details.append({"source": item.source, "destination": item.destination, "status": "success"})
            except Exception as e:
                failed += 1
                details.append({"source": item.source, "destination": item.destination, "status": f"failed: {str(e)}"})

        return OrganizationExecutionReport(
            target_directory=plan.target_directory,
            total_files_processed=len(plan.moves),
            successful_moves=successful,
            failed_moves=failed,
            details=details,
        )
