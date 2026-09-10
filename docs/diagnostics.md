# Deterministic Diagnostic Engine

## Subsystem Diagnostic Routines
- **Filesystem**: Checks target file/directory existence, permissions, readability, and candidate matches.
- **Shell**: Inspects exit code, stderr output snippets, and timeout status.
- **Resource**: Reads current CPU usage, RAM utilization, and available memory in MB.
- **Applications**: Verifies process existence and active window titles.
- **Browser**: Checks current page URL and DOM readiness.
- **Vision**: Verifies screen image hashes and target coordinates.
