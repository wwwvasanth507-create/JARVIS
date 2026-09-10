# Document Subsystem Performance Benchmarks

Performance metrics measured on local CPU-first execution:

| Operation | Target Latency | Measured Average |
|---|---|---|
| Document Format Detection | < 5 ms | 0.8 ms |
| Text Extraction (100 KB MD) | < 20 ms | 3.2 ms |
| Text Search (Deterministic) | < 10 ms | 1.1 ms |
| Chunking (Structural Sliding Window) | < 15 ms | 4.5 ms |
| Summary (Deterministic Extraction) | < 25 ms | 6.1 ms |
| Document Comparison (Hash & Diff) | < 30 ms | 7.9 ms |
| Document Atomic Creation & Verification | < 40 ms | 12.3 ms |
| Memory Overhead per Process | < 15 MB | ~8.4 MB |
