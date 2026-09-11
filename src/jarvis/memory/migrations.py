"""
Database Schema Migrator for JARVIS Memory architecture.
"""

from jarvis.memory.database import DatabaseManager


class SchemaMigrator:
    """Manages SQLite table initialization and schema versions."""

    INIT_SCHEMA_V1 = """
    CREATE TABLE IF NOT EXISTS schema_migrations (
        version INTEGER PRIMARY KEY,
        applied_at REAL NOT NULL
    );

    CREATE TABLE IF NOT EXISTS memories (
        id TEXT PRIMARY KEY,
        type TEXT NOT NULL,
        key TEXT NOT NULL UNIQUE,
        content TEXT NOT NULL,
        metadata_json TEXT DEFAULT '{}',
        source TEXT NOT NULL DEFAULT 'USER_EXPLICIT',
        confidence TEXT NOT NULL DEFAULT 'EXPLICIT',
        importance REAL NOT NULL DEFAULT 1.0,
        created_at REAL NOT NULL,
        updated_at REAL NOT NULL,
        last_accessed_at REAL NOT NULL,
        expires_at REAL,
        privacy_level TEXT NOT NULL DEFAULT 'PERSONAL',
        access_count INTEGER NOT NULL DEFAULT 0
    );

    CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(type);
    CREATE INDEX IF NOT EXISTS idx_memories_key ON memories(key);
    CREATE INDEX IF NOT EXISTS idx_memories_updated ON memories(updated_at);
    CREATE INDEX IF NOT EXISTS idx_memories_expires ON memories(expires_at);

    CREATE TABLE IF NOT EXISTS memory_access (
        id TEXT PRIMARY KEY,
        memory_id TEXT NOT NULL,
        accessed_at REAL NOT NULL,
        query TEXT,
        FOREIGN KEY(memory_id) REFERENCES memories(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS memory_tags (
        memory_id TEXT NOT NULL,
        tag TEXT NOT NULL,
        PRIMARY KEY(memory_id, tag),
        FOREIGN KEY(memory_id) REFERENCES memories(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS projects (
        project_id TEXT PRIMARY KEY,
        name TEXT NOT NULL UNIQUE,
        path TEXT NOT NULL,
        description TEXT DEFAULT '',
        status TEXT NOT NULL DEFAULT 'ACTIVE',
        tags_json TEXT DEFAULT '[]',
        last_used REAL NOT NULL
    );

    CREATE INDEX IF NOT EXISTS idx_projects_name ON projects(name);
    CREATE INDEX IF NOT EXISTS idx_projects_path ON projects(path);

    CREATE TABLE IF NOT EXISTS tasks (
        task_id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        description TEXT DEFAULT '',
        status TEXT NOT NULL DEFAULT 'TODO',
        priority INTEGER NOT NULL DEFAULT 1,
        project_id TEXT,
        created_at REAL NOT NULL,
        updated_at REAL NOT NULL,
        due_at REAL,
        FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE SET NULL
    );

    CREATE TABLE IF NOT EXISTS conversation_summaries (
        id TEXT PRIMARY KEY,
        summary TEXT NOT NULL,
        important_entities_json TEXT DEFAULT '[]',
        active_tasks_json TEXT DEFAULT '[]',
        important_decisions_json TEXT DEFAULT '[]',
        related_project TEXT,
        created_at REAL NOT NULL
    );

    CREATE TABLE IF NOT EXISTS episodes (
        id TEXT PRIMARY KEY,
        description TEXT NOT NULL,
        importance REAL NOT NULL DEFAULT 0.5,
        subsystem TEXT NOT NULL DEFAULT 'generic',
        action TEXT NOT NULL DEFAULT 'observation',
        created_at REAL NOT NULL
    );

    CREATE TABLE IF NOT EXISTS knowledge_documents (
        document_id TEXT PRIMARY KEY,
        path TEXT NOT NULL UNIQUE,
        title TEXT NOT NULL,
        category TEXT NOT NULL DEFAULT 'general',
        tags_json TEXT DEFAULT '[]',
        content_hash TEXT NOT NULL,
        sections_json TEXT DEFAULT '[]',
        created_at REAL NOT NULL,
        updated_at REAL NOT NULL,
        indexed_at REAL NOT NULL
    );

    CREATE INDEX IF NOT EXISTS idx_knowledge_path ON knowledge_documents(path);
    CREATE INDEX IF NOT EXISTS idx_knowledge_category ON knowledge_documents(category);

    CREATE TABLE IF NOT EXISTS knowledge_indexes (
        id TEXT PRIMARY KEY,
        document_id TEXT NOT NULL,
        section_title TEXT,
        content_excerpt TEXT NOT NULL,
        keywords_json TEXT DEFAULT '[]',
        FOREIGN KEY(document_id) REFERENCES knowledge_documents(document_id) ON DELETE CASCADE
    );
    """

    INIT_SCHEMA_V2 = """
    CREATE TABLE IF NOT EXISTS goals (
        goal_id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        description TEXT DEFAULT '',
        owner TEXT NOT NULL DEFAULT 'USER',
        created_at REAL NOT NULL,
        updated_at REAL NOT NULL,
        status TEXT NOT NULL DEFAULT 'DRAFT',
        priority TEXT NOT NULL DEFAULT 'NORMAL',
        deadline REAL,
        deadline_type TEXT NOT NULL DEFAULT 'SOFT',
        time_window_json TEXT DEFAULT '{}',
        constraints_json TEXT DEFAULT '{}',
        dependencies_json TEXT DEFAULT '[]',
        success_criteria_json TEXT DEFAULT '[]',
        risk_level TEXT NOT NULL DEFAULT 'LOW',
        resource_budget_json TEXT DEFAULT '{}',
        progress REAL NOT NULL DEFAULT 0.0,
        progress_confidence TEXT NOT NULL DEFAULT 'MEDIUM',
        autonomy_level INTEGER NOT NULL DEFAULT 1,
        associated_project TEXT,
        associated_memories_json TEXT DEFAULT '[]'
    );

    CREATE INDEX IF NOT EXISTS idx_goals_status ON goals(status);
    CREATE INDEX IF NOT EXISTS idx_goals_priority ON goals(priority);
    CREATE INDEX IF NOT EXISTS idx_goals_owner ON goals(owner);

    CREATE TABLE IF NOT EXISTS objectives (
        objective_id TEXT PRIMARY KEY,
        goal_id TEXT NOT NULL,
        title TEXT NOT NULL,
        description TEXT DEFAULT '',
        status TEXT NOT NULL DEFAULT 'PENDING',
        dependencies_json TEXT DEFAULT '[]',
        completion_criteria_json TEXT DEFAULT '[]',
        verification_json TEXT DEFAULT '{}',
        created_at REAL NOT NULL,
        updated_at REAL NOT NULL,
        FOREIGN KEY(goal_id) REFERENCES goals(goal_id) ON DELETE CASCADE
    );

    CREATE INDEX IF NOT EXISTS idx_objectives_goal ON objectives(goal_id);

    CREATE TABLE IF NOT EXISTS goal_checkpoints (
        checkpoint_id TEXT PRIMARY KEY,
        goal_id TEXT NOT NULL,
        state_json TEXT NOT NULL DEFAULT '{}',
        verified_outputs_json TEXT NOT NULL DEFAULT '[]',
        blockers_json TEXT NOT NULL DEFAULT '[]',
        resource_usage_json TEXT NOT NULL DEFAULT '{}',
        created_at REAL NOT NULL,
        FOREIGN KEY(goal_id) REFERENCES goals(goal_id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS goal_logs (
        log_id TEXT PRIMARY KEY,
        goal_id TEXT NOT NULL,
        event_type TEXT NOT NULL,
        description TEXT NOT NULL,
        data_json TEXT DEFAULT '{}',
        created_at REAL NOT NULL,
        FOREIGN KEY(goal_id) REFERENCES goals(goal_id) ON DELETE CASCADE
    );
    """

    def __init__(self, db_manager: DatabaseManager):
        self.db_mgr = db_manager

    def migrate(self) -> None:
        with self.db_mgr.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("CREATE TABLE IF NOT EXISTS schema_migrations (version INTEGER PRIMARY KEY, applied_at REAL NOT NULL);")
            cur.execute("SELECT MAX(version) FROM schema_migrations;")
            row = cur.fetchone()
            current_version = row[0] if row and row[0] is not None else 0

            if current_version < 1:
                self.db_mgr.execute_script(self.INIT_SCHEMA_V1)
                with self.db_mgr.get_connection() as conn2:
                    conn2.execute("INSERT OR REPLACE INTO schema_migrations (version, applied_at) VALUES (1, unixepoch());")
                    conn2.commit()

            if current_version < 2:
                self.db_mgr.execute_script(self.INIT_SCHEMA_V2)
                with self.db_mgr.get_connection() as conn3:
                    conn3.execute("INSERT OR REPLACE INTO schema_migrations (version, applied_at) VALUES (2, unixepoch());")
                    conn3.commit()
