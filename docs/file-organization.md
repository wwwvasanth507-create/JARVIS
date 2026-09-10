# File Organization Subsystem

JARVIS supports automated file organization workflows through a mandatory multi-phase process to prevent unintended file movements.

## Workflow Phases

1. **Inspect**: Scan directory contents and identify file semantic types (PDF, Markdown, Code, Image, Archive, Executable).
2. **Categorize**: Map file categories to target destination structures (e.g., `Documents/PDFs`, `Pictures`, `Archives`).
3. **Plan**: Generate an `OrganizationPlan` summary detailing all proposed moves and file counts.
4. **Confirm**: Present the plan to the Boss and request explicit authorization for bulk moves (> 5 files).
5. **Execute**: Move files individually according to the approved plan.
6. **Verify**: Inspect and confirm each move result.
