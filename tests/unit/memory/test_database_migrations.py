"""
Unit tests for DatabaseManager and SchemaMigrator.
"""

from jarvis.memory.database import DatabaseManager
from jarvis.memory.migrations import SchemaMigrator


def test_database_initialization():
    db_mgr = DatabaseManager(db_path=":memory:")
    conn = db_mgr.get_connection()
    assert conn is not None
    conn.close()


def test_schema_migrator():
    db_mgr = DatabaseManager(db_path=":memory:")
    migrator = SchemaMigrator(db_mgr)
    migrator.migrate()

    with db_mgr.get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = {row["name"] for row in cur.fetchall()}

    expected = {
        "schema_migrations",
        "memories",
        "memory_access",
        "memory_tags",
        "projects",
        "tasks",
        "conversation_summaries",
        "episodes",
        "knowledge_documents",
        "knowledge_indexes",
    }
    assert expected.issubset(tables)
