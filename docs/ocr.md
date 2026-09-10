# Local OCR Engine Documentation

## Overview
The OCR subsystem provides local CPU-first text extraction from captured screen images or cropped window regions.

## Provider Architecture
`OCRProvider` offers:
- `is_available()`: Checks backend presence (pytesseract or fallback lightweight engine).
- `extract_text(image)`: Returns raw extracted string.
- `extract_regions(image)`: Returns list of `OCRTextRegion` objects (`text`, `confidence`, `x`, `y`, `width`, `height`).

## Confidence Thresholds
- **HIGH (>= 0.85)**: Highly reliable text, safe for direct computer control binding.
- **MEDIUM (0.60 - 0.84)**: Moderately reliable text, requires secondary verification before action.
- **LOW (< 0.60)**: Unreliable text, rejected for safety-critical UI clicks.

## Result Caching
`OCRResultCache` caches extracted OCR regions using perceptual dHash and region bounds to prevent duplicate OCR passes on static screens.
