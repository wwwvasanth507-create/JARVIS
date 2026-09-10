# JARVIS Filesystem Subsystem Architecture

The Filesystem Subsystem provides JARVIS with controlled, deterministic, CPU-first access to the local computer's storage within strict security and permission boundaries.

## Architecture Overview

```
User Request / Natural Language Prompt
         │
         ▼
Tool Subsystem (`filesystem.*` tools)
         │
         ▼
`FilesystemManager` (Central Orchestrator)
    ├── `PathResolver` (Confinement & Traversal Protection)
    ├── `SensitivityChecker` (Protected & Credential Path Detection)
    ├── `FilesystemPermissionChecker` (Policy & Risk Level Evaluation)
    ├── `FileReader` (Safe Text Slicing & Encoding Detection)
    ├── `FileWriter` (Atomic Writes & Overwrite Protection)
    ├── `FileEditor` (Targeted Edits, Backups & State Diffs)
    ├── `FileSearchEngine` (Multi-criteria Search with Exclusions)
    ├── `DuplicateFinder` (Staged 3-Pass Hash Comparison)
    ├── `StorageInfoProvider` (Storage Statistics)
    ├── `FileOperations` (Copy, Move, Rename, Delete with Rollback Log)
    ├── `FileOrganizer` (Inspect -> Categorize -> Plan -> Confirm -> Execute)
    └── `OperationVerifier` (Post-Execution State Verification)
```

## Key Capabilities

1. **Path Safety & Confinement**: Dynamic root expansion (`~`, `%USERPROFILE%`), path traversal block (`../`), device path rejection (`NUL`, `CON`, `\\.\`), and symbolic link escape prevention.
2. **Permission Model**: Strict risk tiers (LOW, MEDIUM, HIGH, CRITICAL) integrated with central security policy. Destructive actions default to prohibited or require confirmation.
3. **Atomic Writes**: Temporary file writing with hash check and atomic swap (`os.replace`). Overwrite protection prevents accidental data loss.
4. **Targeted Editing**: Direct string, line-range, append, and structured JSON key edits with automatic pre-edit backup creation.
5. **Multi-criteria Search**: Resource-capped search filtering by filename pattern, extension, modification timestamp range, file size, and text content.
6. **Staged Duplicate Detection**: Fast 3-stage duplicate detection (Size -> 4KB Partial Hash -> Full SHA-256) preventing memory freezes.
7. **Safe File Organization**: Plan-first organization workflows that require confirmation before bulk file movements.
8. **Verification**: Empirical verification step after every state-changing operation.
