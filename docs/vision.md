# Screen Vision Subsystem

## Overview
The Screen Vision Subsystem gives JARVIS local, CPU-friendly visual screen understanding. It enables active window observation, UI element detection, text recognition (OCR), visual target matching, and before/after visual state verification.

## Component Architecture
- `ScreenVisionManager`: Unified coordinator for screen capture, privacy filtering, OCR, element detection, and visual state comparison.
- `ScreenCapture`: Multi-mode screenshot capture (`FULL_SCREEN`, `ACTIVE_WINDOW`, `REGION`) with fallback synthetic screen generation for headless environments.
- `ScreenPrivacyPolicy`: Blacklists sensitive applications (password managers, banking, lock screens, credential windows) and redacts/refuses visual processing.
- `OCRProvider`: Local CPU-compatible OCR engine extracting structured text regions (`OCRTextRegion`) with confidence scoring (`HIGH`, `MEDIUM`, `LOW`).
- `UIElementDetector`: Multi-layered detection strategy (DOM / Accessibility → OCR → Deterministic visual matching → Local VLM).
- `ScreenComparator`: Performs lightweight before/after screen state comparison using perceptual dHash, OCR delta, and element changes.
- `VisionProvider`: Standard model lifecycle interface (`load`, `unload`, `analyze`, `describe`, `detect`) for local vision models (Moondream, Florence-2).

## Hardware Awareness & Intelligent Routing
1. Simple text request → OCR
2. Known UI element → OCR + template / geometry matching
3. Unknown visual layout → Lightweight vision analysis
4. Complex visual reasoning → Local VLM (only when loaded/configured)

## Privacy & Security Constraints
- Local-first & CPU-first execution.
- No cloud vision or external API calls.
- Privacy exclusions strictly enforced before capture.
- Screen contents treated as untrusted data to prevent visual prompt injection.
