"""
Document verification manager.
"""

import os
from typing import Dict, Any, Tuple
from jarvis.documents.detector import DocumentDetector
from jarvis.documents.registry import DocumentRegistry


class DocumentVerificationManager:
    """
    Verifies document files for existence, non-zero size, readability, and structural integrity.
    """

    def __init__(self, detector: Optional[DocumentDetector] = None, registry: Optional[DocumentRegistry] = None):
        self.detector = detector or DocumentDetector()
        self.registry = registry or DocumentRegistry()

    def verify_created_document(self, path: str, expected_extension: str) -> Dict[str, Any]:
        """
        Verifies created document file.
        """
        if not os.path.exists(path):
            return {"verified": False, "reason": f"File '{path}' does not exist."}

        size = os.path.getsize(path)
        if size == 0:
            return {"verified": False, "reason": f"File '{path}' is 0 bytes."}

        is_readable, msg = self.verify_file_readability(path, expected_extension)
        if not is_readable:
            return {"verified": False, "reason": f"File '{path}' is not readable: {msg}"}

        return {"verified": True, "path": path, "size": size}

    def verify_file_readability(self, path: str, extension: str) -> Tuple[bool, str]:
        """
        Verifies that format reader can parse the file without throwing syntax/format exceptions.
        """
        try:
            reader = self.registry.get_reader(extension)
            reader.extract_structure(path)
            return True, "Success"
        except Exception as e:
            return False, str(e)
