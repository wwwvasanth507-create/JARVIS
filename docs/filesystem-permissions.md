# Filesystem Permission Policy Framework

Filesystem operations map directly into JARVIS's permission hierarchy:

| Risk Tier | Operations | Required Permission Category | Confirmation Policy |
| :--- | :--- | :--- | :--- |
| **LOW** | `list_directory`, `read_file`, `search_files`, `get_metadata`, `find_duplicates`, `get_storage_info` | `READ_FILES` | Pre-approved for safe local roots |
| **MEDIUM** | `create_file`, `create_directory`, `copy_file`, `move_file`, `rename_file` | `WRITE_FILES` | Logged auto-execution within allowed roots |
| **HIGH** | `write_file` (overwrite), `edit_file`, bulk operations, `organize` | `WRITE_FILES` | Requires explicit Boss confirmation |
| **CRITICAL** | `delete_file`, `delete_directory` (recursive), system path changes | `DELETE_FILES` / `SYSTEM_CONTROL` | Requires explicit interactive confirmation |

## Configuration (`config/filesystem.yaml`)

Permissions are managed via declarative policy:

```yaml
filesystem:
  enabled: true
  allow_read: true
  allow_create: true
  allow_write: true
  allow_move: true
  allow_copy: true
  allow_delete: false
```
