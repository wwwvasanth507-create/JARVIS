# JARVIS — Modular Skill & Capability System

The Skill Subsystem (`src/jarvis/skills/`) provides a safe, declarative capability architecture enabling JARVIS to extend its workflows without modifying core orchestrator code.

---

## Key Architecture Concepts

1. **Declarative Manifests**: Skills are defined via `skill.yaml` manifests residing in `skills/builtin/`, `skills/system/`, `skills/user/`, and `skills/experimental/`.
2. **Tool Composition**: Skills compose existing registered tools (`application.*`, `filesystem.*`, `browser.*`, `shell.*`, `computer.*`) into multi-step workflows.
3. **No Arbitrary Code Execution**: Skills DO NOT contain executable Python scripts or dynamic code evaluation. All steps invoke standard registered tools.
4. **Permission Intersection**: Skill permissions are evaluated as the strict intersection of `User Permission ∩ Skill Permission ∩ Tool Permission ∩ System Policy`. Privileges cannot be elevated.
5. **Effective Risk Escalation**: If a LOW-risk skill incorporates a HIGH-risk tool, the effective skill risk level automatically escalates to HIGH, requiring user confirmation.
6. **Deterministic Skill Resolution**: `SkillResolver` maps intents and queries to skills via exact intent match, explicit aliases, or tool capability matches.
7. **Lifecycle Controls**: Skills can be discovered, validated, enabled, or disabled at runtime via `skill.*` tools (`skill.list`, `skill.enable`, `skill.disable`, `skill.status`).

---

## Architecture Flow

```text
User Request / Voice Input
         ↓
Orchestrator Intent Parsing
         ↓
Skill Resolver (Intents, Aliases, Capabilities)
         ↓
Skill Manifest (`skill.yaml`)
         ↓
Skill Safety Policy & Effective Risk Escalation
         ↓
Plan Construction (Skill Workflow Steps -> Plan)
         ↓
Permission Evaluator & Confirmation Manager
         ↓
Plan Executor (Standard Tool Registry Execution)
         ↓
Post-Condition Verification
```
