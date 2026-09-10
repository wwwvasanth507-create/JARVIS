# Knowledge Indexing & Scaling Strategy

The Knowledge Indexer (`src/jarvis/memory/indexing.py`) prepares JARVIS to eventually scale up to **10,000+ Markdown knowledge files** on CPU hardware.

---

## Incremental Indexing Algorithm

1. **Scan Directory**: Discovers `*.md` files across configured knowledge roots.
2. **SHA256 Content Hashing**: Computes document hash. Compares against `knowledge_documents.content_hash`.
3. **Change Delta Detection**: If hash matches existing record, file is skipped immediately.
4. **Section Parsing**: Parses `#` and `##` Markdown headings into discrete sections.
5. **Excerpt Indexing**: Populates `knowledge_indexes` table with section titles and 500-character excerpts.
