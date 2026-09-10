# Document Creation Engine

- **Atomic Writes**: Writes to a temporary staging file, validates format readability, performs atomic rename/replace, and verifies target file.
- **Overwrite Protection**: Detects pre-existing files and raises `DocumentCreationError` unless `overwrite=True` is explicitly specified.
- **Verification**: `DocumentVerificationManager` checks target existence, non-zero byte size, and format parser readability.
