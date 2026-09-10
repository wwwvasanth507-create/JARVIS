# Skill Security & Defense-in-Depth

The Skill Subsystem is designed with zero-trust safety principles (`src/jarvis/skills/safety.py`, `permissions.py`).

---

## Safety Principles

1. **No Code Execution**: Skills cannot execute arbitrary Python scripts or shell strings directly. They can only compose standard registered tools.
2. **Effective Risk Escalation**: Effective risk level is calculated dynamically:
   $$\text{Effective Risk} = \max(\text{Skill Risk}, \max_{t \in \text{Tools}} \text{Tool Risk}(t))$$
   A skill declaring `LOW` risk that uses a `HIGH` risk tool (e.g. `shell.execute` or `filesystem.delete`) automatically escalates to `HIGH` risk.
3. **Confirmation Enforcement**: High-risk skills trigger `ConfirmationManager` requiring explicit user token approval.
4. **Tool-Level Authority**: Tools enforce their own path safety, shell parsing, and permission checks. A skill cannot override or disable tool-level security.
