# Knowledge Base Architecture

JARVIS maintains a distinction between **Personal Memory** (user preferences, project paths, tasks) and **Technical Knowledge** (reference documentation, procedures, system guides).

---

## Technical Knowledge Storage

Knowledge files are stored as structured Markdown documents:

```text
knowledge/
├── systems/
├── programming/
├── applications/
├── websites/
├── troubleshooting/
└── procedures/
```

The Knowledge Subsystem indexes Markdown files incrementally using content hashing, section extraction, and keyword indexing without loading full file contents into memory.
