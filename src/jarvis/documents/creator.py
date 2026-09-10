"""
Safe atomic document creation engine with overwrite protection.
"""

import os
import tempfile
import json
import csv
import io
from typing import Dict, Any, Optional
from jarvis.documents.errors import DocumentCreationError
from jarvis.documents.verification import DocumentVerificationManager


class DocumentCreator:
    """
    Creates documents using atomic temp writes and overwrite protection.
    """

    def __init__(self, verifier: Optional[DocumentVerificationManager] = None):
        self.verifier = verifier or DocumentVerificationManager()

    def create_document(
        self,
        target_path: str,
        content: str,
        format_type: str = "md",
        overwrite: bool = False
    ) -> Dict[str, Any]:
        """
        Creates a new document at target_path.
        """
        target_path = os.path.abspath(target_path)
        if os.path.exists(target_path) and not overwrite:
            raise DocumentCreationError(
                f"Target document path '{target_path}' already exists and overwrite=False."
            )

        target_dir = os.path.dirname(target_path)
        if not os.path.exists(target_dir):
            os.makedirs(target_dir, exist_ok=True)

        ext = os.path.splitext(target_path)[1].lower() or f".{format_type.lower()}"

        # 1. Generate temp file
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=ext, encoding="utf-8") as tmp:
            tmp_path = tmp.name
            tmp.write(content)

        try:
            # 2. Validate temp file format readability
            is_valid, err_msg = self.verifier.verify_file_readability(tmp_path, ext)
            if not is_valid:
                raise DocumentCreationError(f"Generated document failed validation: {err_msg}")

            # 3. Atomic replace/rename
            if os.path.exists(target_path):
                os.remove(target_path)
            os.rename(tmp_path, target_path)

            # 4. Verify target file
            verify_res = self.verifier.verify_created_document(target_path, ext)
            if not verify_res["verified"]:
                raise DocumentCreationError(f"Document verification failed after write: {verify_res['reason']}")

            return {
                "path": target_path,
                "size": os.path.getsize(target_path),
                "created": True,
                "verified": True
            }

        except Exception as e:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
            if isinstance(e, DocumentCreationError):
                raise
            raise DocumentCreationError(f"Failed to create document: {str(e)}")
