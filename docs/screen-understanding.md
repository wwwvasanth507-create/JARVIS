# Screen Understanding Architecture

## Pipeline Flow
```
Screen → Capture → Preprocessing → OCR / Vision → Structured ScreenState → Computer Tools → Verification
```

## Layered Element Detection
JARVIS resolves UI elements using hierarchical strategies to minimize CPU overhead:
1. Accessibility / Native Window API: Interrogates OS controls directly.
2. DOM Integration: Prefers web page DOM elements when operating in browser windows.
3. Local OCR: Reads text labels and bounding boxes on screen.
4. Deterministic Visual Matching: Uses spatial layout analysis and geometric matching.
5. Vision Model / Local VLM: Invoked only for complex visual reasoning on unknown layouts.
