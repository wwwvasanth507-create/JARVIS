# Application Semantics & Family Adapters

## Semantic State Adapter (`src/jarvis/applications/application_semantics.py`)
Replaces binary running/not-running checks with rich application semantic state:
- `busy/idle`
- `modal_present`
- `document_open`
- `has_unsaved_changes`
- `ready_status`

### Application Families Supported:
- Web Browsers
- File Explorers
- Text Editors
- Terminals
- PDF Viewers
- Office Editors
