"""
Document Intelligence & Local Document Processing package.
"""

from jarvis.documents.errors import (
    DocumentError,
    UnsupportedDocumentFormatError,
    OCRRequiredError,
    DocumentSecurityError,
    DocumentLimitExceededError,
    DocumentCreationError,
    DocumentConversionError,
)
from jarvis.documents.models import (
    DocumentInfo,
    DocumentChunk,
    DocumentStructure,
    ExtractedTable,
    DocumentSummary,
    DocumentAnswer,
    DocumentComparison,
)
from jarvis.documents.detector import DocumentDetector
from jarvis.documents.registry import DocumentRegistry
from jarvis.documents.reader import DocumentReader
from jarvis.documents.normalizer import DocumentNormalizer
from jarvis.documents.chunker import DocumentChunker
from jarvis.documents.metadata import DocumentMetadataExtractor
from jarvis.documents.summarizer import DocumentSummarizer
from jarvis.documents.analyzer import DocumentAnalyzer
from jarvis.documents.comparer import DocumentComparer
from jarvis.documents.creator import DocumentCreator
from jarvis.documents.converter import DocumentConverter
from jarvis.documents.tables import TableExtractor
from jarvis.documents.security import DocumentSecurityPolicy
from jarvis.documents.privacy import DocumentPrivacyManager
from jarvis.documents.cache import DocumentCache
from jarvis.documents.verification import DocumentVerificationManager
from jarvis.documents.manager import DocumentManager

__all__ = [
    "DocumentError",
    "UnsupportedDocumentFormatError",
    "OCRRequiredError",
    "DocumentSecurityError",
    "DocumentLimitExceededError",
    "DocumentCreationError",
    "DocumentConversionError",
    "DocumentInfo",
    "DocumentChunk",
    "DocumentStructure",
    "ExtractedTable",
    "DocumentSummary",
    "DocumentAnswer",
    "DocumentComparison",
    "DocumentDetector",
    "DocumentRegistry",
    "DocumentReader",
    "DocumentNormalizer",
    "DocumentChunker",
    "DocumentMetadataExtractor",
    "DocumentSummarizer",
    "DocumentAnalyzer",
    "DocumentComparer",
    "DocumentCreator",
    "DocumentConverter",
    "TableExtractor",
    "DocumentSecurityPolicy",
    "DocumentPrivacyManager",
    "DocumentCache",
    "DocumentVerificationManager",
    "DocumentManager",
]
