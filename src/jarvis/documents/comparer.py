"""
Document comparison and diff engine.
"""

from typing import Optional
from jarvis.documents.models import DocumentInfo, DocumentComparison, DocumentStructure
from jarvis.documents.reader import DocumentReader
from jarvis.documents.registry import DocumentRegistry


class DocumentComparer:
    """
    Compares two documents deterministically using hashes, structural headings, and section diffs.
    """

    def __init__(self, registry: Optional[DocumentRegistry] = None):
        self.registry = registry or DocumentRegistry()

    def compare(self, path_a: str, info_a: DocumentInfo, path_b: str, info_b: DocumentInfo) -> DocumentComparison:
        """
        Compares doc_a and doc_b.
        """
        if info_a.content_hash == info_b.content_hash:
            return DocumentComparison(
                document_a_id=info_a.document_id,
                document_b_id=info_b.document_id,
                semantic_summary="Documents are byte-for-byte identical."
            )

        reader_a = self.registry.get_reader(info_a.extension)
        reader_b = self.registry.get_reader(info_b.extension)

        struct_a = reader_a.extract_structure(path_a)
        struct_b = reader_b.extract_structure(path_b)

        titles_a = {s.get("title", ""): s.get("content", "") for s in struct_a.sections}
        titles_b = {s.get("title", ""): s.get("content", "") for s in struct_b.sections}

        added = [t for t in titles_b if t not in titles_a and t]
        removed = [t for t in titles_a if t not in titles_b and t]

        changed = []
        for t in titles_a:
            if t in titles_b and titles_a[t] != titles_b[t]:
                changed.append({
                    "section_title": t,
                    "length_diff": len(titles_b[t]) - len(titles_a[t])
                })

        struct_diffs = []
        if len(struct_a.headings) != len(struct_b.headings):
            struct_diffs.append(f"Heading count differs: {len(struct_a.headings)} vs {len(struct_b.headings)}")

        return DocumentComparison(
            document_a_id=info_a.document_id,
            document_b_id=info_b.document_id,
            added_sections=added,
            removed_sections=removed,
            changed_sections=changed,
            structural_differences=struct_diffs,
            semantic_summary=f"Compared '{info_a.filename}' and '{info_b.filename}'. Added {len(added)} sections, removed {len(removed)} sections, modified {len(changed)} sections."
        )
