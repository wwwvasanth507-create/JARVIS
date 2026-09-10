# Filesystem Security Architecture

JARVIS adheres to strict security principles to guarantee that filesystem interactions remain safe, isolated, and bounded.

## Confinement Rules

1. **Allowed Roots**: All path requests must resolve within explicitly configured directories (`config/filesystem.yaml`). Attempts to target files outside allowed roots raise `PathOutsideAllowedRoot`.
2. **Protected Roots**: Core operating system directories (`C:\Windows`, `/etc`, `/usr`, `/sys`, etc.) are protected from modification or access, raising `ProtectedPath`.
3. **Sensitive Pattern Detection**: Accessing credentials (`.pem`, `.key`, `id_rsa`), environment secrets (`.env`), password stores (`.kdbx`), or wallet files requires explicit user approval or is blocked by default.
4. **Traversal & Device Guarding**: Paths containing null bytes, path traversal (`../`), or Windows reserved device names (`CON`, `NUL`, `AUX`) raise `InvalidPath`.

## Destructive Action Protection

- Deletion of files or directories is disabled by default (`allow_delete: false`).
- Overwriting existing files requires the explicit `overwrite=True` parameter and MEDIUM/HIGH risk permission approval.
- Bulk operations require multi-step planning and Boss approval before execution.
