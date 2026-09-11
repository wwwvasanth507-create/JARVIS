# Action Execution Guidelines

Guidelines for system, computer, browser, shell, and filesystem operations:
1. **Safety First**: Verify path boundaries and permissions before executing file or process operations.
2. **Reversibility**: Prefer non-destructive actions whenever possible; backup data before mutating files.
3. **No Unsanitized Inputs**: Redact sensitive secrets, keys, and credentials from logs and outputs.
4. **Graceful Handling**: Respect unsaved user work in desktop applications before closing processes.
