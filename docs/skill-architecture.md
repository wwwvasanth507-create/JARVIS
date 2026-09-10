# Skill System Architecture & Package Structure

The Skill subsystem is organized under `src/jarvis/skills/` with declarative manifests located in `skills/`.

---

## Directory Organization

```text
src/jarvis/skills/
├── __init__.py          # Package exports
├── manager.py           # Central SkillManager facade
├── registry.py          # SkillRegistry maintaining active skills & lookup tables
├── loader.py            # SkillLoader parsing and verifying manifests
├── resolver.py          # SkillResolver mapping Intents to Skills
├── models.py            # SkillDefinition, SkillWorkflowStep, SkillQueryResult
├── manifest.py          # SkillManifestParser loading YAML files
├── validator.py         # SkillValidator enforcing schema & tool existence
├── permissions.py       # SkillPermissionChecker evaluating intersection
├── safety.py            # SkillSafetyPolicy computing effective risk escalation
├── executor.py          # SkillExecutor delegating to core PlanExecutor
├── planner.py           # SkillPlanner converting workflows to Plans
├── discovery.py         # SkillDiscovery scanning directory structures
├── dependencies.py      # SkillDependencyManager evaluating tool prerequisites
├── versioning.py        # SkillVersionManager semantic versioning checks
├── lifecycle.py         # SkillLifecycleManager managing state transitions
└── errors.py            # Skill domain exception hierarchy
```

---

## Skill Categories

* **`builtin`**: Trusted skills shipped with core JARVIS (`open_application`, `find_file`, `open_file`, `web_search`, `system_status`).
* **`system`**: Internal skills required for core operations.
* **`user`**: Custom declarative skills created by the Boss.
* **`experimental`**: Disabled by default until explicitly enabled.
