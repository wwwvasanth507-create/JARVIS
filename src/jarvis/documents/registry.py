"""
Extensible document reader registry.
"""

from typing import Dict, Optional, Type
from jarvis.documents.reader import DocumentReader
from jarvis.documents.extractor import (
    PlainTextExtractor,
    MarkdownExtractor,
    JSONYAMLExtractor,
    CSVExtractor,
    HTMLExtractor,
    PDFExtractor,
    DOCXExtractor,
)
from jarvis.documents.errors import UnsupportedDocumentFormatError


class DocumentRegistry:
    """
    Registry mapping document extensions to DocumentReader implementations.
    """

    def __init__(self):
        self._readers: Dict[str, DocumentReader] = {}
        self._register_defaults()

    def _register_defaults(self):
        txt_reader = PlainTextExtractor()
        md_reader = MarkdownExtractor()
        json_yaml_reader = JSONYAMLExtractor()
        csv_reader = CSVExtractor()
        html_reader = HTMLExtractor()
        pdf_reader = PDFExtractor()
        docx_reader = DOCXExtractor()

        self.register(".txt", txt_reader)
        self.register(".md", md_reader)
        self.register(".json", json_yaml_reader)
        self.register(".yaml", json_yaml_reader)
        self.register(".yml", json_yaml_reader)
        self.register(".csv", csv_reader)
        self.register(".html", html_reader)
        self.register(".xml", html_reader)
        self.register(".pdf", pdf_reader)
        self.register(".docx", docx_reader)

    def register(self, extension: str, reader: DocumentReader) -> None:
        ext = extension.lower()
        if not ext.startswith("."):
            ext = f".{ext}"
        self._readers[ext] = reader

    def get_reader(self, extension: str) -> DocumentReader:
        ext = extension.lower()
        if not ext.startswith("."):
            ext = f".{ext}"

        if ext not in self._readers:
            raise UnsupportedDocumentFormatError(f"No document reader registered for format: '{ext}'")

        return self._readers[ext]
