# JARVIS Computer Security & Safety Policy

## Security Principles
1. **No Direct Execution**: The LLM model is never granted raw shell access or arbitrary Python execution for computer control. All actions are routed through structured tool schemas.
2. **Permission Check Enforcement**: Every computer tool call executes `PermissionEvaluator.evaluate()` against `config/permissions.yaml` before performing OS operations.
3. **Structured Input Validation**: Keypresses and hotkeys are validated against strict Virtual Key (VK) lookup tables (`WindowsKeyboard.KEY_MAP`). Unrecognized key specifiers are rejected with status `"DENIED"`.
4. **Graceful Application Closure**: Applications are closed gracefully via `WM_CLOSE` messages by default. Process termination (`force=True`) is restricted to higher risk evaluation.
5. **Screenshot Privacy**: Screenshots are processed in-memory or saved ephemerally in scratch storage, and released immediately after use.
6. **Prohibited Security Violations**: Security policy explicitly prohibits:
   - Credential harvesting or password extraction
   - Disabling security software
   - Stealth persistence or unauthorized remote access
   - Destructive mass file deletions or system alterations
