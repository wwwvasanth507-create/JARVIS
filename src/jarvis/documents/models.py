"""
Document data models.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional


@dataclass
class DocumentInfo:
    document_id: str
    path: str
    filename: str
    extension: str
    mime_type: str
    size: int
    created_at: float
    modified_at: float
    content_hash: str
    page_count: int = 1
    encoding: str = "utf-8"
    language: Optional[str] = None
    is_binary: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DocumentChunk:
    chunk_id: str
    document_id: str
    index: int
    content: str
    start_char: int
    end_char: int
    page_number: Optional[int] = None
    section_title: Optional[str] = None
    token_count: int = 0
    content_hash: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DocumentStructure:
    title: Optional[str] = None
    headings: List[Dict[str, Any]] = field(default_factory=list) # [{level, text, line_number/page}]
    sections: List[Dict[str, Any]] = field(default_factory=list) # [{title, content, page}]
    paragraphs: List[str] = field(default_factory=list)
    code_blocks: List[Dict[str, str]] = field(default_factory=list)
    links: List[Dict[str, str]] = field(default_factory=list)
    tables: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class ExtractedTable:
    table_id: str
    headers: List[str]
    rows: List[List[Any]]
    source_location: str # e.g. "page 3", "section Methods"
    document_id: Optional[str] = None
    caption: Optional[str] = None


@dataclass
class DocumentSummary:
    document_id: str
    summary_text: str
    key_points: List[str] = field(default_factory=list)
    section_summaries: Dict[str, str] = field(default_factory=dict)
    is_llm_generated: bool = False


@dataclass
class DocumentAnswer:
    question: str
    answer: str
    confidence: float
    sources: List[Dict[str, Any]] = field(default_factory=list) # [{page, section, snippet}]
    document_id: str = ""


@dataclass
class DocumentComparison:
    document_a_id: str
    document_b_id: str
    added_sections: List[str] = field(default_factory=list)
    removed_sections: List[str] = field(default_factory=list)
    changed_sections: List[Dict[str, Any]] = field(default_factory=list)
    changed_values: List[Dict[str, Any]] = field(default_factory=list)
    structural_differences: List[str] = field(default_factory=list)
    semantic_summary: Optional[str] = None
