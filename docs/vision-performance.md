# Vision Subsystem Performance Optimization

## CPU Efficiency Strategies
- **Event-Driven Capture**: Screen understanding runs on-demand or during action execution, never continuously polling or rendering.
- **Change Detection**: Perceptual dHash comparison skips OCR and analysis if the screen state has not meaningfully changed (similarity >= 0.95).
- **Region Cropping**: Captures active window or target bounding box instead of full desktop when target context is known.
- **Result Caching**: `OCRResultCache` retains recent text extractions indexed by perceptual hash and region bounds.

## Benchmark Tracking
Performance metrics are stored in `data/cache/vision-benchmark.json`:
- Screenshot capture latency: ~12.4 ms
- Perceptual hash change detection: ~3.2 ms
- OCR throughput: ~450 chars/sec
- Spatial matching: ~8.5 ms
