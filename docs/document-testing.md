# Document Testing Strategy

The document subsystem is tested across unit and integration levels:
- `tests/unit/documents/`: 8 test suites verifying detection, extractors, chunker, normalizer, summarizer, analyzer, comparer, creator, converter, security, privacy, and tools.
- `tests/integration/documents/`: End-to-end integration scenarios verifying end-to-end reading, Q&A grounding, diffing, tool creation, format conversion, and prompt injection neutralization.
