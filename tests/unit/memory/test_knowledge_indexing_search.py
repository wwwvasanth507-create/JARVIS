"""
Unit tests for KnowledgeIndexer and KnowledgeRetriever.
"""

from pathlib import Path
from jarvis.memory.database import DatabaseManager
from jarvis.memory.indexing import KnowledgeIndexer
from jarvis.memory.migrations import SchemaMigrator
from jarvis.memory.retrieval import KnowledgeRetriever


def test_knowledge_indexing_and_search(tmp_path: Path):
    db_mgr = DatabaseManager(db_path=":memory:")
    SchemaMigrator(db_mgr).migrate()

    indexer = KnowledgeIndexer(db_mgr)
    retriever = KnowledgeRetriever(db_mgr)

    # Create dummy markdown file
    doc_path = tmp_path / "jarvis_guide.md"
    doc_path.write_text(
        "# JARVIS Architecture Guide\n\n## Overview\nJARVIS is a local-first AI computer agent running on CPU hardware.\n\n## Memory\nIt features persistent SQLite memory storage.\n",
        encoding="utf-8",
    )

    # Index doc
    doc1 = indexer.index_file(doc_path, category="architecture")
    assert doc1 is not None
    assert doc1.title == "JARVIS Architecture Guide"

    # Search knowledge
    results = retriever.search("local-first computer agent", category="architecture")
    assert len(results) >= 1
    assert "Overview" in results[0].excerpt

    # Re-indexing unchanged file returns None
    doc_unchanged = indexer.index_file(doc_path, category="architecture")
    assert doc_unchanged is None
