"""
Incremental Knowledge Base Indexer for JARVIS.
"""

import hashlib
import json
import os
import re
import time
from pathlib import Path
from typing import List, Optional
from jarvis.memory.database import DatabaseManager
from jarvis.memory.models import KnowledgeDocument


class KnowledgeIndexer:
    """Indexes Markdown knowledge files incrementally via SHA256 content hashing."""

    def __init__(self, db_manager: DatabaseManager):
        self.db_mgr = db_manager

    def index_directory(self, root_dir: str | Path, category: str = "general") -> List[KnowledgeDocument]:
        root_path = Path(root_dir)
        if not root_path.exists():
            return []

        indexed_docs = []
        for file_path in root_path.rglob("*.md"):
            doc = self.index_file(file_path, category=category)
            if doc:
                indexed_docs.append(doc)
        return indexed_docs

    def index_file(self, file_path: str | Path, category: str = "general") -> Optional[KnowledgeDocument]:
        path_obj = Path(file_path).resolve()
        if not path_obj.exists() or not path_obj.is_file():
            return None

        content = path_obj.read_text(encoding="utf-8", errors="replace")
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

        # Check existing hash to avoid unnecessary re-indexing
        with self.db_mgr.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT content_hash FROM knowledge_documents WHERE path = ?", (str(path_obj),))
            row = cur.fetchone()
            if row and row["content_hash"] == content_hash:
                # File unchanged
                return None

        # Parse title & sections
        lines = content.splitlines()
        title = path_obj.stem.replace("-", " ").replace("_", " ").title()
        if lines and lines[0].startswith("# "):
            title = lines[0].lstrip("# ").strip()

        sections = self._extract_sections(content)
        now = time.time()

        doc = KnowledgeDocument(
            path=str(path_obj),
            title=title,
            category=category,
            content_hash=content_hash,
            sections=sections,
            created_at=now,
            updated_at=now,
            indexed_at=now,
        )

        self._save_knowledge_doc(doc)
        return doc

    def _extract_sections(self, content: str) -> List[dict]:
        sections = []
        current_heading = "Overview"
        current_text = []

        for line in content.splitlines():
            if line.startswith("#"):
                if current_text:
                    sections.append({
                        "heading": current_heading,
                        "content": "\n".join(current_text).strip(),
                    })
                    current_text = []
                current_heading = line.lstrip("#").strip()
            else:
                current_text.append(line)

        if current_text:
            sections.append({
                "heading": current_heading,
                "content": "\n".join(current_text).strip(),
            })

        return sections

    def _save_knowledge_doc(self, doc: KnowledgeDocument) -> None:
        with self.db_mgr.get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO knowledge_documents (
                    document_id, path, title, category, tags_json, content_hash,
                    sections_json, created_at, updated_at, indexed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    doc.document_id,
                    doc.path,
                    doc.title,
                    doc.category,
                    json.dumps(doc.tags),
                    doc.content_hash,
                    json.dumps(doc.sections),
                    doc.created_at,
                    doc.updated_at,
                    doc.indexed_at,
                ),
            )
            # Clear old indexes for doc
            conn.execute("DELETE FROM knowledge_indexes WHERE document_id = ?", (doc.document_id,))
            for sec in doc.sections:
                conn.execute(
                    "INSERT INTO knowledge_indexes (id, document_id, section_title, content_excerpt) VALUES (hex(randomblob(8)), ?, ?, ?)",
                    (doc.document_id, sec["heading"], sec["content"][:500]),
                )
            conn.commit()
