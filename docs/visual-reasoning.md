# Local Visual Reasoning & VLM Integration 2.0

JARVIS provides optical text extraction and local visual model reasoning with CPU resource safety bounds.

## Local CPU OCR (`OCRProvider`)

- Multi-language support for English (`en`), Tamil (`ta`), and mixed content.
- Region-of-Interest (ROI) cropping before text extraction.
- Preprocessing contrast enhancement using PIL ImageEnhance.

## Optional Local VLM (`VLMPerceptionAdapter`)

- **Resource Arbitration**: Lazy loads and evaluates memory limits before inference (`ResourceArbitrator`).
- **ROI Reasoning**: Crops screenshots to specific regions (dialog, table, form panel) before running VLM to minimize CPU/RAM usage.
- **Untrusted Perception Safety**: VLM text predictions are treated strictly as untrusted perception data (`confidence=0.45`). VLM outputs NEVER directly trigger side-effect actions without passing through the Target Resolver, Permission Evaluator, and Verification Engine.
