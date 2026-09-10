# Multi-Step Planning & Validation

The Planning subsystem (`src/jarvis/core/orchestration/planner.py`, `plan.py`, `policy.py`) constructs and validates structured execution plans.

---

## Plan Structure

Each `Plan` contains a list of `PlanStep` items:

* `step_id`: Unique identifier
* `description`: Human-readable summary
* `tool_name`: Target tool registered in tool registry
* `arguments`: Structured JSON parameters
* `dependencies`: List of preceding `step_id` dependencies
* `risk_level`: Assigned risk tier (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`)
* `permission`: Required permission category
* `status`: Step lifecycle state (`PENDING`, `WAITING_FOR_CONFIRMATION`, `EXECUTING`, `COMPLETED`, `FAILED`, `CANCELLED`, `SKIPPED`)

---

## Validation & Prohibited Tool Combinations

Before execution, `PlanValidator` verifies:
1. **Tool Existence**: Tool is registered in `ALL_TOOLS`.
2. **Dependency Resolution**: All dependency step IDs exist in the plan.
3. **Security Policy**: Action parameters satisfy `PermissionEvaluator`.
4. **Prohibited Chaining**: Prevents dangerous tool combinations (such as reading sensitive files and immediately piping into shell execution to bypass filesystem root bounds).
