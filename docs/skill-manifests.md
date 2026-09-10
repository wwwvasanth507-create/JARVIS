# Skill Manifest Schema & Format

Skills are declared strictly using YAML manifests named `skill.yaml`.

---

## Example `skill.yaml`

```yaml
skill:
  id: open_application
  name: Open Application
  version: 1.0.0
  description: Opens a desktop application safely with health verification.
  category: builtin
  author: JARVIS Core

  aliases:
    - launch application
    - start application
    - open app

  intents:
    - application.open

  tools:
    - application.find
    - application.open
    - application.health

  permissions:
    - APPLICATION_CONTROL

  risk_level: LOW
  enabled: true

workflow:
  - id: find_app
    action: application.find
    description: Find candidate application in registry

  - id: launch_app
    action: application.open
    description: Launch application process
    depends_on:
      - find_app

  - id: verify_health
    action: application.health
    description: Verify application startup and responsiveness
    depends_on:
      - launch_app
```

---

## Validation Rules

1. `id` must be unique and match `^[a-z0-9_]+$`.
2. `version` must use semantic versioning (`MAJOR.MINOR.PATCH`).
3. Every declared `tool` must exist in `ALL_TOOLS`.
4. Workflow step actions must be registered tools.
