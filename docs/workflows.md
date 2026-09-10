# JARVIS Workflows Architecture

## Overview
The Workflow Engine (`src/jarvis/core/workflows/engine.py`, `templates.py`) provides structured workflow management for daily computer agent tasks across desktop apps, files, browser sessions, and background monitors.

---

## Workflow Lifecycle & States

11 explicit workflow states:
- `DRAFT`: Initial template definition
- `READY`: Validated and ready for execution
- `RUNNING`: Step-by-step tool execution active
- `WAITING_FOR_USER`: Waiting for Boss input/parameter
- `WAITING_FOR_CONFIRMATION`: High-risk step awaiting user confirmation
- `PAUSED`: Paused by user or background pause request
- `RECOVERING`: Attempting failure diagnosis or replanning
- `PARTIAL_SUCCESS`: Some steps succeeded, non-critical steps failed
- `COMPLETED`: All steps executed and verified
- `FAILED`: Execution stopped due to error
- `CANCELLED`: Cancelled by user

---

## Workflow Templates (`WorkflowTemplateRegistry`)
- `research_and_save`: Web search -> Summarize -> Write file
- `find_and_summarize_file`: File search -> Inspect -> Summarize
- `organize_downloads`: Scan directory -> Propose organization -> Move files
- `browser_research`: Open browser -> Navigate -> Extract content
- `scheduled_report`: Schedule recurring task via scheduler
