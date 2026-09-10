"""
Data models and Enums for JARVIS Memory & Knowledge architecture.
"""

import time
import uuid
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class MemoryType(str, Enum):
    FACT = "FACT"
    PREFERENCE = "PREFERENCE"
    PROFILE = "PROFILE"
    PROJECT = "PROJECT"
    LOCATION = "LOCATION"
    TASK = "TASK"
    EPISODIC = "EPISODIC"
    CONVERSATION_SUMMARY = "CONVERSATION_SUMMARY"
    SYSTEM_CONTEXT = "SYSTEM_CONTEXT"


class PrivacyLevel(str, Enum):
    PUBLIC = "PUBLIC"
    PERSONAL = "PERSONAL"
    PRIVATE = "PRIVATE"
    SENSITIVE = "SENSITIVE"


class MemoryConfidence(str, Enum):
    EXPLICIT = "EXPLICIT"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class TaskStatus(str, Enum):
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    BLOCKED = "BLOCKED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class MemoryItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: MemoryType = MemoryType.FACT
    key: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    source: str = "USER_EXPLICIT"
    confidence: MemoryConfidence = MemoryConfidence.EXPLICIT
    importance: float = 1.0  # 0.0 to 1.0 scale
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)
    last_accessed_at: float = Field(default_factory=time.time)
    expires_at: Optional[float] = None
    privacy_level: PrivacyLevel = PrivacyLevel.PERSONAL
    access_count: int = 0


class ConversationSummary(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    summary: str
    important_entities: List[str] = Field(default_factory=list)
    active_tasks: List[str] = Field(default_factory=list)
    important_decisions: List[str] = Field(default_factory=list)
    related_project: Optional[str] = None
    created_at: float = Field(default_factory=time.time)


class Episode(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    description: str
    importance: float = 0.5
    subsystem: str = "generic"
    action: str = "observation"
    created_at: float = Field(default_factory=time.time)


class ProjectRecord(BaseModel):
    project_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    path: str
    description: str = ""
    status: str = "ACTIVE"
    tags: List[str] = Field(default_factory=list)
    last_used: float = Field(default_factory=time.time)


class TaskRecord(BaseModel):
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str = ""
    status: TaskStatus = TaskStatus.TODO
    priority: int = 1
    project_id: Optional[str] = None
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)
    due_at: Optional[float] = None


class KnowledgeDocument(BaseModel):
    document_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    path: str
    title: str
    category: str = "general"
    tags: List[str] = Field(default_factory=list)
    content_hash: str
    sections: List[Dict[str, str]] = Field(default_factory=list)
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)
    indexed_at: float = Field(default_factory=time.time)


class KnowledgeQueryResult(BaseModel):
    document_id: str
    title: str
    path: str
    category: str
    excerpt: str
    relevance_score: float = 0.0
