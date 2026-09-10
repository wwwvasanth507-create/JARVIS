# File Search Architecture

JARVIS provides fast, deterministic, CPU-friendly file search capability via `filesystem.search`.

## Features

- **Filter Criteria**: Search by filename pattern (`*.pdf`), file extension (`.md`), modification date range, size range, and text content matching.
- **Resource Constraints**:
  - `max_results` (default: 100) prevents sending thousands of results to LLM context.
  - `max_depth` (default: 10) prevents unbounded directory traversal.
  - Default folder exclusions: `.git`, `node_modules`, `__pycache__`, `venv`.
- **Progress Reporting & Cancellation**: Asynchronous traversal supports status callbacks and `threading.Event` cancellation.
