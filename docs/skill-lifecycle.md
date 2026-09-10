# Skill Lifecycle States

Skills transition through formal lifecycle states managed by `SkillLifecycleManager` (`src/jarvis/skills/lifecycle.py`).

---

## State Diagram

```text
  [DISCOVERED]
       │ (Manifest & Schema Parsing)
       ▼
  [VALIDATED] ──(Enabled)──► [ENABLED] ──(Disabled)──► [DISABLED]
       │                         │                         │
       ├─(Missing Dep)───────────┼─────────────────────────┤
       ▼                         ▼                         ▼
 [UNAVAILABLE]               [FAILED]                 [DISABLED]
```

---

## Lifecycle States

* `DISCOVERED`: `skill.yaml` file located in skill directory.
* `VALIDATED`: Schema, tools, and dependencies verified.
* `ENABLED`: Active and available for resolution by `SkillResolver`.
* `DISABLED`: Loaded but inactive; resolution will ignore this skill.
* `UNAVAILABLE`: Missing required tools or subsystems.
* `FAILED`: Manifest parsing or schema validation error.
