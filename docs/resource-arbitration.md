# Subsystem Resource Arbitration

`ResourceArbitrator` (`src/jarvis/system/resource_arbitrator.py`) governs hardware and subsystem resource leases across five categories:
- `MODEL`: Local LLM inference runtime (concurrency limit = 1).
- `BROWSER`: Playwright browser contexts (concurrency limit = 2).
- `VISION`: Screen capture and OCR engine (concurrency limit = 1).
- `VOICE`: STT / TTS engines (concurrency limit = 1).
- `MICROPHONE`: Audio input capture (concurrency limit = 1).

Goals must acquire active leases before executing steps requiring subsystem resources, preventing resource contention or CPU overcommitment.
