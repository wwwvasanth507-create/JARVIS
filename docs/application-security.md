# Application Control Security Architecture

JARVIS implements strict safety boundaries to ensure application management never compromises system stability or user data.

## Security Rules

1. **Ambiguity Protection**: Queries matching multiple distinct applications raise `AmbiguousApplication` and request Boss input rather than picking arbitrarily.
2. **Protected Software Guard**: Security applications (antivirus, firewall, system control) cannot be modified or closed autonomously.
3. **Unsaved Work Protection**: Applications holding unsaved changes report `has_unsaved_work: true` and fail graceful close until explicit force confirmation is granted.
4. **Filesystem Confinement**: Document paths and working directories are validated against Prompt 007's filesystem safety policies.
5. **No Shell Injection**: Applications are launched directly via executable path and structured argument arrays (`subprocess.Popen`), avoiding raw shell concatenation.
