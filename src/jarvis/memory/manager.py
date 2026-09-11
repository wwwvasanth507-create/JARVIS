"""
Central MemoryManager facade for JARVIS Persistent Memory & Knowledge Architecture.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
from jarvis.memory.database import DatabaseManager
from jarvis.memory.deduplication import MemoryDeduplicator
from jarvis.memory.embeddings import EmbeddingProvider
from jarvis.memory.episodes import EpisodeManager
from jarvis.memory.extraction import MemoryExtractor
from jarvis.memory.facts import FactManager
from jarvis.memory.indexing import KnowledgeIndexer
from jarvis.memory.migrations import SchemaMigrator
from jarvis.memory.models import (
    KnowledgeQueryResult,
    MemoryConfidence,
    MemoryItem,
    MemoryType,
    PrivacyLevel,
    ProjectRecord,
    TaskRecord,
    TaskStatus,
)
from jarvis.memory.preferences import PreferenceManager
from jarvis.memory.privacy import MemoryPrivacyPolicy
from jarvis.memory.projects import ProjectManager
from jarvis.memory.ranking import MemoryRanker
from jarvis.memory.retention import RetentionManager
from jarvis.memory.retrieval import KnowledgeRetriever, MemoryRetriever
from jarvis.memory.storage import MemoryStorage
from jarvis.memory.tasks import TaskManager


class MemoryManager:
    """Central unified Memory & Knowledge Subsystem facade."""

    _instance: Optional["MemoryManager"] = None

    @classmethod
    def get_instance(cls, db_path: Optional[str | Path] = None) -> "MemoryManager":
        if cls._instance is None:
            cls._instance = cls(db_path=db_path)
        return cls._instance

    def __init__(self, db_path: Optional[str | Path] = None):
        self.db_mgr = DatabaseManager(db_path=db_path)
        self.migrator = SchemaMigrator(self.db_mgr)
        self.migrator.migrate()

        self.storage = MemoryStorage(self.db_mgr)
        self.privacy_policy = MemoryPrivacyPolicy()
        self.deduplicator = MemoryDeduplicator(self.storage)
        self.embedding_provider = EmbeddingProvider()

        self.preferences = PreferenceManager(self.storage, self.deduplicator)
        self.facts = FactManager(self.storage, self.deduplicator)
        self.episodes = EpisodeManager(self.storage)
        self.projects = ProjectManager(self.storage)
        self.tasks = TaskManager(self.storage)
        self.extractor = MemoryExtractor()
        self.retention = RetentionManager(self.storage)

        self.ranker = MemoryRanker()
        self.retriever = MemoryRetriever(self.storage, self.ranker)
        self.knowledge_indexer = KnowledgeIndexer(self.db_mgr)
        self.knowledge_retriever = KnowledgeRetriever(self.db_mgr)

    # --- High Level Operations ---

    def remember(
        self,
        key: str,
        content: str,
        memory_type: MemoryType = MemoryType.FACT,
        privacy_level: PrivacyLevel = PrivacyLevel.PERSONAL,
        source: str = "USER_EXPLICIT",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MemoryItem:
        item = MemoryItem(
            type=memory_type,
            key=key,
            content=content,
            metadata=metadata or {},
            source=source,
            confidence=MemoryConfidence.EXPLICIT if source == "USER_EXPLICIT" else MemoryConfidence.HIGH,
            privacy_level=privacy_level,
        )
        # 1. Enforce privacy policy (raises PrivacyViolationError if sensitive)
        self.privacy_policy.validate(item)

        # 2. Process deduplication & conflict resolution
        resolved = self.deduplicator.process_and_deduplicate(item)

        # 3. Save to SQL storage
        self.storage.save_memory(resolved)

        # 4. If memory is a project path, auto-register in project manager
        if "project" in key.lower() or memory_type == MemoryType.PROJECT:
            proj_name = key.replace("project_", "").replace("_path", "")
            self.projects.register_project(name=proj_name, path=content)

        return resolved

    def process_user_text_for_memories(self, user_text: str) -> Optional[MemoryItem]:
        extracted = self.extractor.extract_explicit_memory(user_text)
        if extracted:
            key, content, mem_type_str = extracted
            mtype = MemoryType.PROJECT if mem_type_str == "project" else MemoryType.PREFERENCE
            return self.remember(key=key, content=content, memory_type=mtype)
        return None

    def retrieve(self, query: str, limit: int = 5) -> List[MemoryItem]:
        return self.retriever.retrieve(query=query, limit=limit)

    def forget(self, key: str) -> bool:
        norm_key = self.deduplicator.normalize_key(key)
        return self.retention.forget_key(norm_key)

    def list_all_memories(self, limit: int = 100) -> List[MemoryItem]:
        return self.storage.list_memories(limit=limit)

    # --- Preferences & Projects Shortcut APIs ---

    def set_preference(self, key: str, value: str) -> MemoryItem:
        item = MemoryItem(
            type=MemoryType.PREFERENCE,
            key=f"pref_{key}",
            content=value,
            metadata={"pref_name": key},
            privacy_level=PrivacyLevel.PERSONAL,
        )
        self.privacy_policy.validate(item)
        return self.preferences.set_preference(key=key, value=value)

    def get_preference(self, key: str) -> Optional[str]:
        return self.preferences.get_preference(key)

    def register_project(self, name: str, path: str, description: str = "") -> ProjectRecord:
        return self.projects.register_project(name=name, path=path, description=description)

    def get_project(self, name: str) -> Optional[ProjectRecord]:
        return self.projects.get_project(name)

    # --- Knowledge Subsystem Operations ---

    def index_knowledge_directory(self, dir_path: str | Path, category: str = "general") -> int:
        docs = self.knowledge_indexer.index_directory(dir_path, category=category)
        return len(docs)

    def search_knowledge(self, query: str, category: Optional[str] = None, limit: int = 5) -> List[KnowledgeQueryResult]:
        return self.knowledge_retriever.search(query=query, category=category, limit=limit)

    def search_memory(self, query: str, limit: int = 10) -> List[MemoryItem]:
        return self.retrieve(query=query, limit=limit)

    def get_all_memories(self, category: Optional[str] = None, limit: int = 100) -> List[MemoryItem]:
        items = self.list_all_memories(limit=limit)
        if category:
            return [i for i in items if i.type.value.lower() == category.lower()]
        return items

    def get_memory_by_key(self, key: str) -> Optional[MemoryItem]:
        items = self.storage.list_memories(limit=500)
        norm = self.deduplicator.normalize_key(key)
        for i in items:
            if i.key == norm or i.key == key:
                return i
        return None

    def get_memory_by_id(self, item_id: str) -> Optional[MemoryItem]:
        items = self.storage.list_memories(limit=500)
        for i in items:
            if i.id == item_id:
                return i
        return None

    def forget_memory(self, key_or_id: str) -> bool:
        item = self.get_memory_by_key(key_or_id) or self.get_memory_by_id(key_or_id)
        if item:
            return self.forget(item.key)
        return self.forget(key_or_id)

    def forget_by_category(self, category: str) -> int:
        items = self.get_all_memories(category=category, limit=500)
        count = 0
        for i in items:
            if self.forget(i.key):
                count += 1
        return count
