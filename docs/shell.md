# JARVIS Controlled Shell Subsystem Architecture

The Shell Subsystem provides JARVIS with controlled, deterministic, permission-evaluated command-line capability across Windows, Linux, and macOS.

## Architecture Overview

```
LLM / Agent Request
         │
         ▼
Tool Registry (`shell.*` tools)
         │
         ▼
`ShellManager` (Central Orchestrator)
    ├── `CommandParser` (Tokenization & Operator Detection)
    ├── `DangerousCommandDetector` (Destructive & Privilege Escalation Guard)
    ├── `CommandValidator` (Allowlist/Denylist & Working Dir Confinement)
    ├── `ShellPermissionChecker` (Policy & Risk Tier Evaluation)
    ├── `ShellEnvironment` (Platform Detection & Secret Redaction)
    ├── `ShellExecutor` (Subprocess Execution, Output Capping, Timeouts)
    ├── `JobCanceller` (Process Handle & Graceful Termination)
    ├── `ProcessManager` (Safe Non-sensitive Process Inspection & Termination)
    ├── `CommandVerifier` (Empirical Outcome Verification)
    └── `AuditRecord` (Security & Operations Audit Trail)
```

## Key Capabilities

1. **Safety & Policy Confinement**: Validates executable against allowlist/denylist in `config/shell.yaml`, enforces working directory boundaries via Prompt 007's filesystem allowed roots, and redacts sensitive environment variables (`*_PASSWORD`, `*_TOKEN`, `*_SECRET`, `*_KEY`).
2. **Zero Autonomous Privilege Escalation**: Autonomous requests for `sudo`, `su`, `runas`, or UAC bypasses are blocked.
3. **Dangerous Command Protection**: System destruction (`format`, `rm -rf /`, `rd /s /q c:\`), shutdown/reboot, firewall/antivirus tampering, and credential harvesting utilities (`mimikatz`, `pwdump`) are strictly blocked.
4. **Output & Resource Capping**: Subprocess stdout/stderr outputs are capped (`max_stdout_bytes`, `max_output_lines`), commands have strict timeouts, and background jobs are tracked via `ShellJob` lifecycle states (`QUEUED`, `RUNNING`, `COMPLETED`, `FAILED`, `TIMED_OUT`, `CANCELLED`).
5. **Empirical Verification**: Verifies exit codes, output pattern matches, artifact creation, or active listening process states.
