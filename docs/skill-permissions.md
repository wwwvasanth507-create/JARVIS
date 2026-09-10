# Skill Permissions & Privilege Intersection

Skills operate under strict permission intersection rules (`src/jarvis/skills/permissions.py`).

---

## Intersection Principle

```text
Granted Skill Capability = User Policy
                          ∩ Skill Declared Permissions
                          ∩ Underlying Tool Requirements
                          ∩ System Security Policy
```

---

## Non-Elevation Rule

A skill manifest cannot grant a permission category that the primary user security configuration (`config/permissions.yaml`) prohibits. If any tool required by a skill violates the security policy, `SkillPermissionDeniedError` is raised and the skill is blocked.
