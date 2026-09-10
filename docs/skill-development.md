# Skill Development Guide for the Boss

Creating a new skill in JARVIS requires zero core Python changes. Simply create a directory under `skills/user/` with a `skill.yaml` file.

---

## Step-by-Step Skill Creation

1. Create a directory: `skills/user/my_custom_skill/`
2. Create `skills/user/my_custom_skill/skill.yaml`:

```yaml
skill:
  id: my_custom_skill
  name: Custom Workflow
  version: 1.0.0
  description: Performs custom user workflow.
  category: user

  aliases:
    - my workflow

  intents:
    - custom.action

  tools:
    - filesystem.search
    - application.open_file

  permissions:
    - READ_FILES
    - APPLICATION_CONTROL

  risk_level: LOW

workflow:
  - id: step_search
    action: filesystem.search
    description: Search files

  - id: step_open
    action: application.open_file
    description: Open result
    depends_on:
      - step_search
```

3. JARVIS will discover and register the skill automatically on startup or via `SkillManager.discover_and_load_all()`.
