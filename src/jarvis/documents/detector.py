"""
Document format detection and file signature analysis.
"""

import os
try:
    import magic
except ImportError:
    magic = None
from typing import Dict, Any, Tuple, Optional

from jarvis.documents.errors import UnsupportedDocumentFormatError


SUPPORTED_FORMATS = {
    ".txt": ("text/plain", "text"),
    ".md": ("text/markdown", "text"),
    ".json": ("application/json", "text"),
    ".yaml": ("application/x-yaml", "text"),
    ".yml": ("application/x-yaml", "text"),
    ".csv": ("text/csv", "text"),
    ".html": ("text/html", "text"),
    ".xml": ("application/xml", "text"),
    ".pdf": ("application/pdf", "binary"),
    ".docx": ("application/vnd.openxmlformats-officedocument.wordprocessingml.document", "binary"),
}

# Magic bytes signatures
MAGIC_SIGNATURES = [
    (b"%PDF", ".pdf", "application/pdf"),
    (b"PK\x03\x04", ".docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"), # or zip based
]


class DocumentDetector:
    """
    Detects file format, mime type, and classification using extensions and byte signatures.
    """

    def detect(self, path: str) -> Dict[str, Any]:
        """
        Detects file metadata and format.
        """
        if not os.path.exists(path):
            raise FileNotFoundError(f"Document file not found: {path}")

        ext = os.path.splitext(path)[1].lower()
        
        # Check magic bytes first if binary candidate or missing ext
        sniffed_ext, sniffed_mime = self._sniff_magic_bytes(path)
        
        final_ext = sniffed_ext if sniffed_ext else ext
        
        if final_ext not in SUPPORTED_FORMATS:
            raise UnsupportedDocumentFormatError(
                f"Unsupported document format '{final_ext}' for file: {path}"
            )

        mime_type, classification = SUPPORTED_FORMATS[final_ext]
        is_binary = (classification == "binary")

        return {
            "extension": final_ext,
            "mime_type": sniffed_mime if sniffed_mime else mime_type,
            "classification": classification,
            "is_binary": is_binary,
            "supported": True
        }

    def _sniff_magic_bytes(self, path: str) -> Tuple[Optional[str], Optional[str]]:
        try:
            with open(path, "rb") as f:
                header = f.read(16)
                for sig, ext, mime in MAGIC_SIGNATURES:
                    if header.startswith(sig):
                        return ext, mime
        except Exception:
            pass
        return None, None
