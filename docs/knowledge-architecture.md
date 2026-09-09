# Scalable Knowledge & Prompt Architecture (10,000+ Markdown Files)

---

## 1. Context Budget Challenge

As **JARVIS** grows to incorporate thousands of skills, prompts, troubleshooting recipes, application manuals, and domain knowledge documents, loading all files directly into the LLM context window is computationally impossible and inefficient.

Local model execution (e.g., GGUF 2K–4K token context) requires strict context budget management:
- **System Identity & Core Instructions**: ~500 tokens
- **Active Task Scratchpad & Recent Turn History**: ~1,000 tokens
- **Available Tool Schemas (Filtered)**: ~500 tokens
- **Retrieved Knowledge / Relevant Skill Snippets**: ~1,000 tokens MAX

---

## 2. Standardized Document Metadata Schema

Every file stored in `knowledge/`, `skills/`, `prompts/`, `workflows/`, etc., MUST begin with a standardized YAML frontmatter header:

```yaml
---
id: "skill-browser-navigation-v1"
type: "skill"               # Options: knowledge, skill, prompt, workflow, troubleshooting, application, website, os
domain: "web_automation"
version: "1.0.0"
risk: "LOW"                 # Options: LOW, MEDIUM, HIGH, CRITICAL
requires:
  - "browser.open"
  - "browser.click"
tags:
  - "playwright"
  - "web"
  - "navigation"
updated: "2026-09-10"
---
```

---

## 3. Directory Layout for Scaled Assets

```text
JARVIS/
├── knowledge/
│   ├── applications/       # App manuals & shortcut maps (e.g. VSCode, Excel, Photoshop)
│   ├── websites/           # DOM maps & interaction recipes for common web portals
│   ├── operating_systems/  # Windows 11 API reference, registry keys, CLI patterns
│   └── domain_rules/       # General knowledge & business rules
├── skills/                 # Multi-step action workflows and tool usage recipes
├── prompts/                # System, planning, execution, verification prompt templates
├── workflows/              # Complex task DAG specifications
└── troubleshooting/        # Known error signatures & mitigation strategies
```

---

## 4. Indexing, Search & Retrieval Architecture

To retrieve relevant documents instantaneously without context bloat, JARVIS uses a 3-tier retrieval pipeline:

```text
                             10,000+ Markdown Files
                                       │
                                       ▼
                       ┌──────────────────────────────┐
                       │ Local Metadata & Indexer     │
                       │ (SQLite FTS5 + Vector Store) │
                       └──────────────┬───────────────┘
                                      │
              ┌───────────────────────┴───────────────────────┐
              ▼                                               ▼
   [ Fast BM25 Keyword Search ]                  [ Local Embedding Search ]
   (Index: tags, id, domain, risk)              (Sentence Transformers / MiniLM)
              │                                               │
              └───────────────────────┬───────────────────────┘
                                      ▼
                       ┌──────────────────────────────┐
                       │ Hybrid Ranker & Reranker     │
                       └──────────────┬───────────────┘
                                      │
                                      ▼
                       ┌──────────────────────────────┐
                       │ Dynamic Context Injector     │
                       │ (Selected Top-K Snippets)     │
                       └──────────────────────────────┘
```

### 4.1 Tier 1: Local Metadata SQLite Index (`data/indexes/metadata.db`)
- At startup or via background file watcher, all YAML frontmatter headers are parsed into a lightweight SQLite table (`fts_knowledge`).
- Metadata filtering allows instant zero-overhead querying by `domain`, `type`, `risk`, `requires`, and `tags`.

### 4.2 Tier 2: Hybrid Retrieval (BM25 + Dense Vector Embeddings)
- **Keyword Search (BM25)**: SQLite FTS5 index searches document titles, headers, and code snippet identifiers.
- **Dense Vector Search**: Small local embedding model (e.g. `all-MiniLM-L6-v2` ONNX CPU backend) generates 384-dimensional embeddings for document chunks.
- Queries extract the top $K$ (e.g., $K = 3$) most relevant snippets.

### 4.3 Tier 3: Dynamic Skill & Prompt Loading
- Skills are lazily loaded into memory **only when a relevant goal triggers them**.
- If a user task asks to "Organize Excel files", only `skills/excel_automation.md` and `knowledge/applications/excel.md` are loaded into context; all 9,998 other files remain unloaded on disk.

---

## 5. Maintenance & Validation Tooling

- Standard validation scripts (`scripts/validate_knowledge.py`) ensure every file adheres to the frontmatter schema, contains valid syntax, and references existent tool names.

---

*Knowledge Scaling Architecture Specification — Phase 1.*
