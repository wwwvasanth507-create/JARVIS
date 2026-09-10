# Application Permission Policy Framework

Application operations map directly into JARVIS's central security framework:

| Risk Tier | Operations | Required Category | Confirmation Policy |
| :--- | :--- | :--- | :--- |
| **LOW** | `application.list`, `application.find`, `application.is_running`, `application.list_running`, `application.health`, `application.list_startup` | `APPLICATION_CONTROL` | Pre-approved for safe queries |
| **MEDIUM** | `application.open`, `application.focus`, `application.open_file`, `application.open_url` | `APPLICATION_CONTROL` | Logged auto-execution within safe roots |
| **HIGH** | `application.close`, `application.restart`, closing apps with unsaved work | `APPLICATION_CONTROL` | Requires explicit Boss confirmation |
| **CRITICAL** | Security software manipulation, privilege escalation attempts | `SYSTEM_CONTROL` | Blocked or interactive confirmation |

## Configuration (`config/applications.yaml`)

```yaml
protected_applications:
  - "Windows Defender"
  - "Antivirus"
  - "Firewall"
  - "Task Manager"
```
