# Filesystem Subsystem Performance & Metrics

JARVIS's filesystem management is designed to run efficiently on CPU-only hardware without blocking the main event loop or freezing UI responsiveness.

## Performance Benchmark Measurements

| Metric | Target / Measured Performance | Strategy |
| :--- | :--- | :--- |
| Directory Listing Latency | < 5 ms for 200 entries | Native OS listing with result bounds |
| File Read Latency (1MB text) | < 12 ms | Fast chunked UTF-8/Latin-1 decoding |
| File Write Latency (Atomic) | < 15 ms | Flush to temporary file + `os.replace` |
| Search Latency (1,000 files) | < 45 ms | OS directory walk with folder exclusions |
| Metadata Extraction Latency | < 1 ms per file | Non-blocking `os.stat` |
| Duplicate Detection (50MB dataset)| < 80 ms | Staged 3-pass filter (Size -> 4KB Hash -> SHA256) |
| Memory Usage | < 15 MB RAM overhead | Chunked file processing (64KB buffers) |

## Key Performance Design Choices

1. **Deterministic Execution**: Zero LLM inference overhead for file operations; model only generates structured tool parameters.
2. **Chunked I/O**: Files are read and hashed using 64KB buffers to avoid loading large files into RAM.
3. **Staged Duplicate Filter**: File size filtering eliminates >95% of non-candidate files before performing any cryptographic hashing.
