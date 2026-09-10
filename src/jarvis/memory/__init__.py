"""
Memory and Persistent Database Package Exports for JARVIS.
"""

from jarvis.memory.database import DatabaseManager
from jarvis.memory.deduplication import MemoryDeduplicator
from jarvis.memory.embeddings import EmbeddingProvider
from jarvis.memory.episodes import EpisodeManager
from jarvis.memory.errors import (
    DatabaseError,
    InvalidMemoryTypeError,
    MemoryError,
    MemoryNotFoundError,
    PrivacyViolationError,
)
from jarvis.memory.extraction import MemoryExtractor
from jarvis.memory.facts import FactManager
from jarvis.memory.indexing import KnowledgeIndexer
from jarvis.memory.manager import MemoryManager
from jarvis.memory.migrations import SchemaMigrator
from jarvis.memory.models import (
    ConversationSummary,
    Episode,
    KnowledgeDocument,
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

__all__ = [
    "MemoryManager",
    "MemoryItem",
    "MemoryType",
    "PrivacyLevel",
    "MemoryConfidence",
    "TaskStatus",
    "ConversationSummary",
    "Episode",
    "ProjectRecord",
    "TaskRecord",
    "KnowledgeDocument",
    "KnowledgeQueryResult",
    "DatabaseManager",
    "SchemaMigrator",
    "MemoryStorage",
    "MemoryPrivacyPolicy",
    "MemoryDeduplicator",
    "PreferenceManager",
    "FactManager",
    "EpisodeManager",
    "ProjectManager",
    "TaskManager",
    "MemoryExtractor",
    "RetentionManager",
    "EmbeddingProvider",
    "KnowledgeIndexer",
    "MemoryRanker",
    "MemoryRetriever",
    "KnowledgeRetriever",
    "MemoryError",
    "DatabaseError",
    "MemoryNotFoundError",
    "PrivacyViolationError",
    "InvalidMemoryTypeError",
]
