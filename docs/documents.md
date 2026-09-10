# Document Intelligence & Local Document Processing Subsystem

The Document Intelligence subsystem provides JARVIS with local-first, CPU-first document inspection, structural text extraction, summarization, Question Answering with source citations, document comparison, table extraction, atomic creation, format conversion, and strict prompt injection security.

## Core Capabilities
- **Local-First & CPU-First**: 0 external AI APIs, 0 cloud services, 0 Ollama dependency.
- **Format Support**: `.txt`, `.md`, `.json`, `.yaml`, `.yml`, `.csv`, `.html`, `.xml`, `.pdf`, `.docx`.
- **Structural Parsing**: Preserves headings, sections, paragraphs, code blocks, links, and tables.
- **Source Grounding**: Provides exact section titles and page numbers for document Q&A.
- **Atomic File Operations**: Overwrite protection, temporary file staging, and post-write verification.
- **Prompt Injection Protection**: `DocumentSecurityPolicy` treats document contents strictly as untrusted data.
