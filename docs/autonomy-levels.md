# Explicit Autonomy Tiers (Levels 0–3)

JARVIS defines four explicit, user-controlled autonomy levels:

### Level 0 — MANUAL
JARVIS acts strictly upon direct, step-by-step user input. Every action requires explicit confirmation.

### Level 1 — ASSISTED (Default)
JARVIS parses intents, constructs proposals, and suggests goals/workflows, but requires user confirmation before executing side-effect steps.

### Level 2 — SUPERVISED
JARVIS executes approved multi-step goals with continuous verification, automatic low-risk step execution, checkpoints, and bounded self-recovery. High and Critical risk actions remain confirmation-gated.

### Level 3 — SCHEDULED
JARVIS executes pre-configured recurring or scheduled background goals under strict CPU, memory, and duration budgets. High and Critical risk actions remain confirmation-gated.

> [!IMPORTANT]
> Higher autonomy levels NEVER grant security bypasses, privilege escalation, or unmonitored persistence.
