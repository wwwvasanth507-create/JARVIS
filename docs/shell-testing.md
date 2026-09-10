# Shell Subsystem Testing Strategy

JARVIS shell testing is partitioned into unit safety verification and non-destructive integration tests.

## Test Suites

1. **Unit Tests (`tests/unit/shell/`)**:
   - `test_parser_validator.py`: Command parsing, tokenization, pipeline operator detection, allowlist/denylist enforcement, working directory validation.
   - `test_shell_safety.py`: Validates that dangerous commands (disk format, root deletion, shutdown, privilege escalation, credential dumping, download-and-execute pipelines) are blocked. *Never executes destructive commands.*
   - `test_executor_jobs.py`: Subprocess execution, output truncation, timeouts, background jobs, and cancellation.
   - `test_environment_processes.py`: Secret redaction in environment variables and safe process listing.
   - `test_shell_tools.py`: Tool registry integration and `BaseTool` wrappers.

2. **Integration Test (`tests/integration/shell/test_shell_integration.py`)**:
   - Executes safe commands (`python --version`, `echo test`) in a temporary directory (`tmp_path`).
   - Verifies command acceptance, permission checking, execution, output capturing, result verification, and audit logging without altering system state.
