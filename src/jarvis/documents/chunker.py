"""
Document chunking engine.
"""

import hashlib
from typing import List, Optional
from jarvis.documents.models import DocumentChunk, DocumentStructure
from jarvis.documents.errors import DocumentLimitExceededError


class DocumentChunker:
    """
    Chunks document content based on structure (sections/paragraphs) into bounded size chunks.
    """

    def __init__(self, chunk_size: int = 1500, chunk_overlap: int = 150, max_chunks: int = 5000):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.max_chunks = max_chunks

    def chunk_text(self, text: str, document_id: str, structure: Optional[DocumentStructure] = None) -> List[DocumentChunk]:
        """
        Chunks text into bounded DocumentChunk objects.
        """
        if not text:
            return []

        chunks: List[DocumentChunk] = []

        # If structural sections are available, chunk by section first
        if structure and structure.sections:
            chunks = self._chunk_by_sections(structure, document_id)
        else:
            chunks = self._chunk_by_paragraphs(text, document_id)

        if len(chunks) > self.max_chunks:
            raise DocumentLimitExceededError(
                f"Generated {len(chunks)} chunks, exceeding max limit of {self.max_chunks}."
            )

        return chunks

    def _chunk_by_sections(self, structure: DocumentStructure, document_id: str) -> List[DocumentChunk]:
        chunks = []
        idx = 0
        char_pos = 0

        for section in structure.sections:
            sec_title = section.get("title", "Untitled Section")
            sec_content = section.get("content", "")
            page_num = section.get("page")

            sec_chunks = self._sliding_window_chunk(
                sec_content, document_id, idx, char_pos, section_title=sec_title, page_number=page_num
            )
            chunks.extend(sec_chunks)
            idx += len(sec_chunks)
            char_pos += len(sec_content) + 1

        return chunks

    def _chunk_by_paragraphs(self, text: str, document_id: str) -> List[DocumentChunk]:
        return self._sliding_window_chunk(text, document_id, 0, 0)

    def _sliding_window_chunk(
        self, text: str, document_id: str, start_index: int, start_char_pos: int,
        section_title: Optional[str] = None, page_number: Optional[int] = None
    ) -> List[DocumentChunk]:
        chunks = []
        idx = start_index
        pos = 0
        text_len = len(text)

        if text_len <= self.chunk_size:
            content = text
            ch_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()[:12]
            return [DocumentChunk(
                chunk_id=f"{document_id}_chk_{idx}",
                document_id=document_id,
                index=idx,
                content=content,
                start_char=start_char_pos,
                end_char=start_char_pos + text_len,
                page_number=page_number,
                section_title=section_title,
                token_count=len(content.split()),
                content_hash=ch_hash
            )]

        while pos < text_len:
            end = pos + self.chunk_size
            if end >= text_len:
                chunk_text = text[pos:]
            else:
                # Find space boundary
                space_pos = text.rfind(" ", pos + self.chunk_size - 100, end)
                if space_pos > pos:
                    end = space_pos
                chunk_text = text[pos:end]

            ch_hash = hashlib.sha256(chunk_text.encode('utf-8')).hexdigest()[:12]
            chunks.append(DocumentChunk(
                chunk_id=f"{document_id}_chk_{idx}",
                document_id=document_id,
                index=idx,
                content=chunk_text,
                start_char=start_char_pos + pos,
                end_char=start_char_pos + pos + len(chunk_text),
                page_number=page_number,
                section_title=section_title,
                token_count=len(chunk_text.split()),
                content_hash=ch_hash
            ))
            idx += 1

            if end >= text_len:
                break
            pos = max(pos + 1, end - self.chunk_overlap)

        return chunks
