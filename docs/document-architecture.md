# Document Subsystem Architecture

```text
Document File
 ↓
DocumentDetector (sniff magic bytes & ext)
 ↓
DocumentMetadataExtractor (size & SHA-256 hash)
 ↓
DocumentRegistry (Format-specific DocumentReader)
 ↓
DocumentNormalizer (Clean whitespace & line endings)
 ↓
DocumentChunker (Structural sliding-window chunking)
 ↓
DocumentAnalyzer / Summarizer / Comparer / TableExtractor
 ↓
DocumentSecurityPolicy (Sanitize & wrap as <UNTRUSTED_DOCUMENT_CONTENT>)
 ↓
Bounded LLM Context / Tool Dispatcher
```
