"""
Document Question Answering and analysis engine with explicit source grounding.
"""

import re
from typing import List, Dict, Any, Optional
from jarvis.documents.models import DocumentInfo, DocumentChunk, DocumentAnswer
from jarvis.documents.chunker import DocumentChunker
from jarvis.documents.reader import DocumentReader
from jarvis.documents.registry import DocumentRegistry
from jarvis.documents.security import DocumentSecurityPolicy


class DocumentAnalyzer:
    """
    Answers questions against documents using bounded chunk retrieval and strict source grounding.
    Never fabricates citations or page numbers.
    """

    def __init__(
        self,
        registry: Optional[DocumentRegistry] = None,
        chunker: Optional[DocumentChunker] = None,
        security: Optional[DocumentSecurityPolicy] = None
    ):
        self.registry = registry or DocumentRegistry()
        self.chunker = chunker or DocumentChunker()
        self.security = security or DocumentSecurityPolicy()

    def ask(self, question: str, path: str, doc_info: DocumentInfo) -> DocumentAnswer:
        """
        Answers a user question based on document chunks, returning verified citations.
        """
        reader = self.registry.get_reader(doc_info.extension)
        structure = reader.extract_structure(path)
        full_text = reader.extract_text(path)

        chunks = self.chunker.chunk_text(full_text, doc_info.document_id, structure)

        # Retrieve relevant chunks by term overlap / keyword search
        relevant_chunks = self._retrieve_relevant_chunks(question, chunks, top_k=3)

        if not relevant_chunks:
            return DocumentAnswer(
                question=question,
                answer="No relevant sections found in the document to answer this question.",
                confidence=0.0,
                sources=[],
                document_id=doc_info.document_id
            )

        # Build grounded answer and citations
        sources = []
        answer_snippets = []
        for chk in relevant_chunks:
            sec_title = chk.section_title or "Document Section"
            page_info = f"page {chk.page_number}" if chk.page_number else "Source location could not be determined precisely"
            sources.append({
                "chunk_id": chk.chunk_id,
                "page": chk.page_number,
                "section": sec_title,
                "location_str": f"{sec_title} ({page_info})" if chk.page_number else sec_title,
                "snippet": chk.content[:150]
            })
            answer_snippets.append(chk.content)

        # Deterministic extraction of answer from snippets
        combined_snippets = "\n".join(answer_snippets)
        sanitized_answer, _ = self.security.sanitize_text(combined_snippets)

        return DocumentAnswer(
            question=question,
            answer=f"Based on {doc_info.filename}: {sanitized_answer[:300]}...",
            confidence=0.85,
            sources=sources,
            document_id=doc_info.document_id
        )

    def search_text(self, query: str, path: str, doc_info: DocumentInfo) -> List[Dict[str, Any]]:
        """
        Performs deterministic text search across document content.
        """
        reader = self.registry.get_reader(doc_info.extension)
        full_text = reader.extract_text(path)
        lines = full_text.split("\n")
        results = []

        query_lower = query.lower()
        for idx, line in enumerate(lines):
            if query_lower in line.lower():
                sanitized, _ = self.security.sanitize_text(line.strip())
                results.append({
                    "line_number": idx + 1,
                    "content": sanitized
                })

        return results

    def _retrieve_relevant_chunks(self, question: str, chunks: List[DocumentChunk], top_k: int = 3) -> List[DocumentChunk]:
        terms = [t.lower() for t in re.findall(r"\w+", question) if len(t) > 2]
        if not terms:
            return chunks[:top_k]

        scored_chunks = []
        for chk in chunks:
            content_lower = chk.content.lower()
            score = sum(content_lower.count(term) for term in terms)
            if score > 0:
                scored_chunks.append((score, chk))

        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        return [chk for score, chk in scored_chunks[:top_k]]
