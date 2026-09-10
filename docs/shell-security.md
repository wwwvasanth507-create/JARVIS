# Shell Subsystem Security Architecture

JARVIS enforces multi-layered defense-in-depth security principles for all terminal operations.

## Security Layers

1. **Allowlist / Denylist Policy**: Executables must be in `allow_commands` (`python`, `git`, `node`, `pip`, etc.) and not in `deny_commands` (`format`, `shutdown`, `reboot`, etc.).
2. **Dangerous Operation Block**: `DangerousCommandDetector` blocks disk formatting, system deletion, shutdown, security software disabling, and credential harvesting utilities.
3. **Zero Privilege Escalation**: Autonomous requests for `sudo`, `su`, or `runas` raise `PrivilegeEscalationBlocked`.
4. **Working Directory Confinement**: Working directories must resolve within allowed root directories from Prompt 007's filesystem layer, raising `InvalidWorkingDirectory` otherwise.
5. **Secret Redaction**: Environment variable values matching sensitive patterns (`*_PASSWORD`, `*_TOKEN`, `*_SECRET`, `*_KEY`) are automatically replaced with `[REDACTED]`.
6. **Download & Execute Pipeline Guard**: Patterns such as `curl ... | sh` or `wget ... | bash` are blocked.
7. **Audit Logging**: Every command execution attempt records an immutable `AuditRecord` containing timestamp, command string, risk level, working directory, exit code, and verification status.
