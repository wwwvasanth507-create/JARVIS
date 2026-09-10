# Document Extraction Engine

The document extraction engine uses format-specific extractors implementing the `DocumentReader` interface to extract raw text and structural metadata:
- **PDF**: Page-by-page text extraction. Emits `OCR_REQUIRED` when 0 text characters are found.
- **DOCX**: Extract headings, paragraphs, lists, tables. 0 macro execution.
- **Markdown**: Heading level hierarchy, sections, paragraphs, code blocks, links, tables.
- **CSV**: Streaming header and row analysis with column statistics.
- **JSON/YAML**: Deterministic dot-notation key lookup (`database.host`) before LLM context insertion.
- **HTML/XML**: Safe parsing with zero JavaScript execution.
