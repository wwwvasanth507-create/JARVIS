# Document Analysis & Question Answering

- **Summarization**: `summarize()`, `summarize_section()`, `summarize_pages()` using deterministic extraction first and bounded local LLM context when needed.
- **Document Q&A**: Question term overlap scoring -> relevant chunk retrieval -> bounded context -> response generation with exact source location citations (page number, section title).
- **Source Grounding**: Never fabricates page numbers. If location is uncertain, returns `"Source location could not be determined precisely"`.
- **Document Comparison**: Hashes documents first; performs section-by-section diff protection to minimize context size.
