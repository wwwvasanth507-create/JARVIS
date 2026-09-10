"""
Central DocumentManager facade.
"""

from typing import Dict, Any, List, Optional, Tuple
from jarvis.documents.models import (
    DocumentInfo, DocumentChunk, DocumentStructure,
    ExtractedTable, DocumentSummary, DocumentAnswer, DocumentComparison
)
from jarvis.documents.detector import DocumentDetector
from jarvis.documents.metadata import DocumentMetadataExtractor
from jarvis.documents.normalizer import DocumentNormalizer
from jarvis.documents.chunker import DocumentChunker
from jarvis.documents.cache import DocumentCache
from jarvis.documents.registry import DocumentRegistry
from jarvis.documents.tables import TableExtractor
from jarvis.documents.summarizer import DocumentSummarizer
from jarvis.documents.analyzer import DocumentAnalyzer
from jarvis.documents.comparer import DocumentComparer
from jarvis.documents.creator import DocumentCreator
from jarvis.documents.converter import DocumentConverter
from jarvis.documents.security import DocumentSecurityPolicy
from jarvis.documents.privacy import DocumentPrivacyManager
from jarvis.documents.verification import DocumentVerificationManager


class DocumentManager:
    """
    Central manager for local document intelligence and processing.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        chunk_size = self.config.get("chunk_size", 1500)
        chunk_overlap = self.config.get("chunk_overlap", 150)
        max_chunks = self.config.get("max_chunks", 5000)
        max_file_size = self.config.get("max_file_size_bytes", 52428800)
        cache_enabled = self.config.get("cache_enabled", True)

        self.detector = DocumentDetector()
        self.metadata_extractor = DocumentMetadataExtractor(self.detector, max_file_size_bytes=max_file_size)
        self.normalizer = DocumentNormalizer()
        self.chunker = DocumentChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap, max_chunks=max_chunks)
        self.cache = DocumentCache(enabled=cache_enabled)
        self.registry = DocumentRegistry()
        self.security = DocumentSecurityPolicy()
        self.privacy = DocumentPrivacyManager()
        self.verifier = DocumentVerificationManager(self.detector, self.registry)

        self.table_extractor = TableExtractor(self.registry)
        self.summarizer = DocumentSummarizer(self.registry, self.security)
        self.analyzer = DocumentAnalyzer(self.registry, self.chunker, self.security)
        self.comparer = DocumentComparer(self.registry)
        self.creator = DocumentCreator(self.verifier)
        self.converter = DocumentConverter(self.registry, self.creator)

    def inspect_document(self, path: str) -> DocumentInfo:
        doc_info = self.metadata_extractor.extract_metadata(path)

        # Update page count from reader
        cached_pages = self.cache.get(doc_info.content_hash, "page_count")
        if cached_pages is not None:
            doc_info.page_count = cached_pages
        else:
            reader = self.registry.get_reader(doc_info.extension)
            meta = reader.read_metadata(path)
            doc_info.page_count = meta.get("page_count", 1)
            self.cache.set(doc_info.content_hash, "page_count", doc_info.page_count)

        return doc_info

    def read_document(self, path: str, page_range: Optional[Tuple[int, int]] = None) -> Dict[str, Any]:
        info = self.inspect_document(path)
        reader = self.registry.get_reader(info.extension)

        cached_text = self.cache.get(info.content_hash, f"text_{page_range}")
        if cached_text is None:
            text = reader.extract_text(path, page_range=page_range)
            text = self.normalizer.normalize(text)
            text, _ = self.security.sanitize_text(text)
            self.cache.set(info.content_hash, f"text_{page_range}", text)
            cached_text = text

        structure = reader.extract_structure(path)
        wrapped_text = self.security.wrap_as_document_content(cached_text, info.document_id)

        return {
            "info": info,
            "text": cached_text,
            "wrapped_text": wrapped_text,
            "structure": structure
        }

    def summarize_document(self, path: str, section_title: Optional[str] = None, page_range: Optional[Tuple[int, int]] = None) -> DocumentSummary:
        info = self.inspect_document(path)
        if section_title:
            return self.summarizer.summarize_section(path, info, section_title)
        elif page_range:
            return self.summarizer.summarize_pages(path, info, page_range)
        return self.summarizer.summarize(path, info)

    def ask_document(self, question: str, path: str) -> DocumentAnswer:
        info = self.inspect_document(path)
        return self.analyzer.ask(question, path, info)

    def search_document(self, query: str, path: str) -> List[Dict[str, Any]]:
        info = self.inspect_document(path)
        return self.analyzer.search_text(query, path, info)

    def compare_documents(self, path_a: str, path_b: str) -> DocumentComparison:
        info_a = self.inspect_document(path_a)
        info_b = self.inspect_document(path_b)
        return self.comparer.compare(path_a, info_a, path_b, info_b)

    def extract_tables(self, path: str) -> List[ExtractedTable]:
        info = self.inspect_document(path)
        return self.table_extractor.extract_tables(path, info.extension)

    def create_document(self, path: str, content: str, format_type: str = "md", overwrite: bool = False) -> Dict[str, Any]:
        return self.creator.create_document(path, content, format_type, overwrite)

    def convert_document(self, source_path: str, target_path: str, overwrite: bool = False) -> Dict[str, Any]:
        return self.converter.convert(source_path, target_path, overwrite)
