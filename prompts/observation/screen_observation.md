# Screen Observation Guidelines

Rules for visual and screen perception:
1. **Source Hierarchy**: Prioritize accessibility DOM handles > app APIs > OCR text > visual features > VLM inferences.
2. **Privacy Masking**: Automatically mask sensitive windows, credential forms, and financial documents.
3. **Spatial Precision**: Ground target locations using exact relative bounding boxes and spatial relationships.
4. **Confidence Scoring**: Require high visual confidence before executing side-effect user input actions.
