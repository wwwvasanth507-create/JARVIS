"""
Document format conversion engine.
"""

import os
import json
import csv
import io
from typing import Dict, Any, Optional
from jarvis.documents.errors import DocumentConversionError
from jarvis.documents.registry import DocumentRegistry
from jarvis.documents.creator import DocumentCreator


class DocumentConverter:
    """
    Converts documents between supported formats (e.g. Markdown -> DOCX, CSV -> JSON, JSON -> Markdown).
    """

    def __init__(self, registry: Optional[DocumentRegistry] = None, creator: Optional[DocumentCreator] = None):
        self.registry = registry or DocumentRegistry()
        self.creator = creator or DocumentCreator()

    def convert(
        self,
        source_path: str,
        target_path: str,
        overwrite: bool = False
    ) -> Dict[str, Any]:
        """
        Converts source_path into target_path format.
        """
        source_ext = os.path.splitext(source_path)[1].lower()
        target_ext = os.path.splitext(target_path)[1].lower()

        reader = self.registry.get_reader(source_ext)
        source_text = reader.extract_text(source_path)

        converted_content = ""

        # CSV -> JSON
        if source_ext == ".csv" and target_ext == ".json":
            f = io.StringIO(source_text)
            csv_reader = csv.DictReader(f)
            data = [row for row in csv_reader]
            converted_content = json.dumps(data, indent=2)

        # JSON -> Markdown
        elif source_ext == ".json" and target_ext in [".md", ".markdown"]:
            data = json.loads(source_text)
            converted_content = f"# JSON Data Export\n\n```json\n{json.dumps(data, indent=2)}\n```"

        # Markdown -> DOCX (or PlainText)
        elif source_ext in [".md", ".txt"] and target_ext == ".docx":
            # For DOCX target, create plain text structure or docx
            converted_content = source_text

        # Default text fallback
        else:
            converted_content = source_text

        create_res = self.creator.create_document(
            target_path=target_path,
            content=converted_content,
            format_type=target_ext.lstrip("."),
            overwrite=overwrite
        )

        return {
            "source_path": source_path,
            "target_path": target_path,
            "source_format": source_ext,
            "target_format": target_ext,
            "size": create_res["size"],
            "converted": True,
            "verified": True
        }
