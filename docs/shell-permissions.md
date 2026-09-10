# Shell Permission Policy Framework

Terminal commands map directly into JARVIS's central security framework:

| Risk Tier | Operations / Executables | Required Category | Confirmation Policy |
| :--- | :--- | :--- | :--- |
| **READ_ONLY / LOW** | Version queries (`python --version`, `git --version`), directory/status inspection (`git status`, `pwd`, `whoami`), `get_environment`, `list_processes` | `RUN_COMMANDS` | Pre-approved for safe allowed directories |
| **MEDIUM** | Project builds, dependency management (`pip install`, `npm install`), non-destructive scripts, job cancellation | `RUN_COMMANDS` / `WRITE_FILES` | Logged execution within allowed roots |
| **HIGH** | Process termination (`terminate_process`), pipeline commands, network-affecting commands (`curl`, `ssh`) | `RUN_COMMANDS` / `NETWORK_ACCESS` | Requires explicit Boss confirmation |
| **CRITICAL** | Privilege escalation requests, destructive system operations, security software changes | `SYSTEM_CONTROL` | Blocked or interactive confirmation |

## Configuration (`config/shell.yaml`)

```yaml
shell:
  enabled: true
  default_timeout: 30
  max_stdout_bytes: 524288
  allow_commands:
    - python
    - git
    - node
    - npm
    - pip
```
