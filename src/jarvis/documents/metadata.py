"""
Document metadata extraction and limit validation.
"""

import os
import hashlib
import uuid
from typing import Dict, Any
from jarvis.documents.models import DocumentInfo
from jarvis.documents.detector import DocumentDetector
from jarvis.documents.errors import DocumentLimitExceededError


class DocumentMetadataExtractor:
    """
    Extracts metadata from local documents without loading large contents unnecessarily.
    """

    def __init__(self, detector: DocumentDetector = None, max_file_size_bytes: int = 52428800):
        self.detector = detector or DocumentDetector()
        self.max_file_size_bytes = max_file_size_bytes

    def extract_metadata(self, path: str) -> DocumentInfo:
        """
        Extracts DocumentInfo metadata.
        """
        stat = os.stat(path)
        if stat.st_size > self.max_file_size_bytes:
            raise DocumentLimitExceededError(
                f"File size {stat.st_size} bytes exceeds maximum limit of {self.max_file_size_bytes} bytes."
            )

        detection = self.detector.detect(path)
        content_hash = self._compute_sha256(path)
        doc_id = f"doc_{content_hash[:16]}"

        return DocumentInfo(
            document_id=doc_id,
            path=path,
            filename=os.path.basename(path),
            extension=detection["extension"],
            mime_type=detection["mime_type"],
            size=stat.st_size,
            created_at=stat.st_ctime,
            modified_at=stat.st_mtime,
            content_hash=content_hash,
            page_count=1, # Default 1, updated by specific readers (e.g. PDF/DOCX)
            encoding="utf-8",
            is_binary=detection["is_binary"],
            metadata={}
        )

    def _compute_sha256(self, path: str) -> str:
        hasher = hashlib.sha256()
        with open(path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest()
