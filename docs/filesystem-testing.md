# Filesystem Subsystem Testing Strategy

JARVIS filesystem testing is strictly partitioned to guarantee that tests NEVER touch or mutate real user files.

## Test Suites

1. **Unit Tests (`tests/unit/filesystem/`)**:
   - `test_paths.py`: Normalization, traversal rejection, reserved device names.
   - `test_safety.py`: Protected OS path detection and sensitive pattern matching.
   - `test_reader_writer.py`: Encoding detection, atomic writing, line slicing, overwrite guards.
   - `test_editor.py`: Target string replacement, JSON key edits, backup file creation.
   - `test_search_duplicates.py`: Multi-criteria file search and staged duplicate detection.
   - `test_operations.py`: Copy, move, rename, delete, rollback log, and storage metrics.
   - `test_organization.py`: Plan generation and execution.
   - `test_filesystem_tools.py`: Integration with ToolRegistry and BaseTool execution.

2. **Integration Test (`tests/integration/filesystem/test_filesystem_integration.py`)**:
   - Executes an end-to-end 13-step file lifecycle within an isolated temporary directory created by `pytest` (`tmp_path`).
   - Verifies path confinement, creation, reading, editing, copying, renaming, moving, searching, deleting, and full cleanup verification.
