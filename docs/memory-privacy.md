# Memory Privacy Policy & Security

The Memory Privacy Policy (`src/jarvis/memory/privacy.py`) enforces strict boundaries on what information can be stored in persistent database files.

---

## Blocked Sensitive Patterns

The memory policy automatically detects and raises `PrivacyViolationError` for:

* **Passwords**: `password=...`, `passwd: ...`
* **API Keys & Tokens**: `api_key=...`, `secret_key=...`, `access_token=...`, `Bearer ...`
* **Private Keys**: `-----BEGIN PRIVATE KEY-----`
* **Credit Cards**: Visa (`4xxx`), Mastercard (`51-55xxx`)
* **Government IDs**: US Social Security Numbers (`xxx-xx-xxxx`)
* **Explicit Sensitive Flag**: `PrivacyLevel.SENSITIVE`

---

## Permission Isolation Rule

Memory is context, NOT permission. Storing a memory record of a path or command does NOT bypass `PermissionEvaluator` or safety checks when executing real-world tool actions.
