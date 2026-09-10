"""
Document summarization engine.
"""

from typing import Optional, Tuple, Dict, Any, List
from jarvis.documents.models import DocumentInfo, DocumentSummary, DocumentStructure
from jarvis.documents.reader import DocumentReader
from jarvis.documents.registry import DocumentRegistry
from jarvis.documents.security import DocumentSecurityPolicy


class DocumentSummarizer:
    """
    Summarizes documents or specific sections using deterministic extraction first,
    and optional local LLM integration when semantic summarization is needed.
    """

    def __init__(self, registry: Optional[DocumentRegistry] = None, security: Optional[DocumentSecurityPolicy] = None):
        self.registry = registry or DocumentRegistry()
        self.security = security or DocumentSecurityPolicy()

    def summarize(self, path: str, doc_info: DocumentInfo) -> DocumentSummary:
        """
        Generates a summary of the full document.
        """
        reader = self.registry.get_reader(doc_info.extension)
        structure = reader.extract_structure(path)

        # Deterministic extraction
        key_points = []
        if structure.title:
            key_points.append(f"Title: {structure.title}")
        if structure.headings:
            key_points.append(f"Key Sections: {', '.join([h['text'] for h in structure.headings[:5]])}")

        if structure.paragraphs:
            summary_text = f"Document '{doc_info.filename}' contains {len(structure.paragraphs)} paragraphs."
            if len(structure.paragraphs) > 0:
                summary_text += f" Overview: {structure.paragraphs[0][:200]}..."
        else:
            raw_text = reader.extract_text(path)
            summary_text = f"Document '{doc_info.filename}' ({doc_info.size} bytes). Snippet: {raw_text[:200]}..."

        # Sanitize summary text
        summary_text, _ = self.security.sanitize_text(summary_text)

        sec_summaries = {}
        for sec in structure.sections[:5]:
            sec_title = sec.get("title", "Section")
            sec_content = sec.get("content", "")
            sec_summaries[sec_title] = sec_content[:150] + "..." if len(sec_content) > 150 else sec_content

        return DocumentSummary(
            document_id=doc_info.document_id,
            summary_text=summary_text,
            key_points=key_points,
            section_summaries=sec_summaries,
            is_llm_generated=False
        )

    def summarize_section(self, path: str, doc_info: DocumentInfo, section_title: str) -> DocumentSummary:
        reader = self.registry.get_reader(doc_info.extension)
        structure = reader.extract_structure(path)

        target_content = ""
        for sec in structure.sections:
            if section_title.lower() in sec.get("title", "").lower():
                target_content = sec.get("content", "")
                break

        if not target_content:
            target_content = f"Section '{section_title}' not found in document."

        sanitized, _ = self.security.sanitize_text(target_content[:300])
        return DocumentSummary(
            document_id=doc_info.document_id,
            summary_text=f"Summary of section '{section_title}': {sanitized}",
            key_points=[f"Target Section: {section_title}"],
            section_summaries={section_title: sanitized},
            is_llm_generated=False
        )

    def summarize_pages(self, path: str, doc_info: DocumentInfo, page_range: Tuple[int, int]) -> DocumentSummary:
        reader = self.registry.get_reader(doc_info.extension)
        page_text = reader.extract_text(path, page_range=page_range)
        sanitized, _ = self.security.sanitize_text(page_text[:300])

        return DocumentSummary(
            document_id=doc_info.document_id,
            summary_text=f"Summary of pages {page_range[0]}-{page_range[1]}: {sanitized}",
            key_points=[f"Page Range: {page_range[0]}-{page_range[1]}"],
            is_llm_generated=False
        )
