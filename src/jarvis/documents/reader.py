"""
Abstract base document reader interface.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple
from jarvis.documents.models import DocumentInfo, DocumentStructure


class DocumentReader(ABC):
    """
    Abstract interface for all format-specific document readers.
    """

    @abstractmethod
    def can_read(self, extension: str, mime_type: str) -> bool:
        """Returns True if this reader handles the given extension/mime."""
        pass

    @abstractmethod
    def read_metadata(self, path: str) -> Dict[str, Any]:
        """Extracts format-specific metadata."""
        pass

    @abstractmethod
    def extract_text(self, path: str, page_range: Optional[Tuple[int, int]] = None) -> str:
        """Extracts text content, optionally bounded by page range (1-indexed)."""
        pass

    @abstractmethod
    def extract_structure(self, path: str) -> DocumentStructure:
        """Extracts structural headings, sections, paragraphs, code blocks, links, tables."""
        pass
