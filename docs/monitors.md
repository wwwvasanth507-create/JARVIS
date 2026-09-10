# Governed Background Condition Monitors

## Monitor Manager (`src/jarvis/system/monitors.py`)
Allows Boss to explicitly request condition monitoring:
- `FILE_EXISTS` ("Tell me when the report appears")
- `FILE_MODIFIED` ("Watch this document for changes")
- `DOWNLOAD_COMPLETE` ("Tell me when the download finishes")
- `APPLICATION_STARTED` ("Notify me when Chrome opens")
- `TASK_FINISHED` ("Alert me when task 123 completes")

## Resource Budgets & Expiration
- Enforces configurable polling intervals (default 2.0s), maximum runtimes (default 1 hour), permission re-checking, and automatic monitor expiration.
