# Memory Architecture & Database Schema

The Memory subsystem is powered by an embedded SQLite database (`data/database/memory.db`) managed by `DatabaseManager` and `SchemaMigrator`.

---

## Database Tables & Schema

### `memories`
* `id`: TEXT PRIMARY KEY
* `type`: TEXT (`FACT`, `PREFERENCE`, `PROJECT`, etc.)
* `key`: TEXT UNIQUE
* `content`: TEXT
* `metadata_json`: TEXT
* `source`: TEXT (`USER_EXPLICIT`, `SYSTEM`, etc.)
* `confidence`: TEXT (`EXPLICIT`, `HIGH`, `MEDIUM`, `LOW`)
* `importance`: REAL (0.0 to 1.0)
* `created_at`, `updated_at`, `last_accessed_at`: REAL
* `expires_at`: REAL (Optional TTL timestamp)
* `privacy_level`: TEXT (`PUBLIC`, `PERSONAL`, `PRIVATE`, `SENSITIVE`)
* `access_count`: INTEGER

### `projects`
* `project_id`: TEXT PRIMARY KEY
* `name`: TEXT UNIQUE
* `path`: TEXT
* `description`: TEXT
* `status`: TEXT
* `tags_json`: TEXT
* `last_used`: REAL

### `tasks`
* `task_id`: TEXT PRIMARY KEY
* `title`: TEXT
* `description`: TEXT
* `status`: TEXT (`TODO`, `IN_PROGRESS`, `BLOCKED`, `COMPLETED`, `CANCELLED`)
* `priority`: INTEGER
* `project_id`: TEXT (Foreign Key)

### `knowledge_documents` & `knowledge_indexes`
* Stores document metadata, SHA256 content hashes, section headings, and text excerpts for incremental search.
