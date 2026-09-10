# Vision Model Lifecycle & Hardware Awareness

## Vision Provider Abstraction
`VisionProvider` standardizes vision model lifecycle management (`load`, `unload`, `analyze`, `describe`, `detect`, `is_available`, `health_check`).

## Hardware Awareness Strategy
- **CPU-Only Systems**: Vision enabled without GPU requirement. Defaults to OCR + spatial layout matching. Avoids large VLM loading at startup.
- **GPU-Accelerated Systems**: Lazy loads small VLMs (Moondream, Florence-2) on demand for complex visual layout analysis.

## Resource Management
- Lazy loading: Vision models loaded only when explicitly needed.
- Image resolution bounds: Automatic downscaling (`max_width: 1280`, `max_height: 720`) prior to VLM processing.
