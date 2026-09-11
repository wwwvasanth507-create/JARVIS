# Unified UI Element & Snapshot Model

JARVIS models desktop and web interfaces using unified, structured data representations.

## Common `UIElement` Model

Fields:
- `id`: Unique string identifier
- `role`: Element role (`button`, `input`, `checkbox`, `radio`, `select`, `table`, `row`, `cell`, `form`, `dialog`, `link`, `text`, `region`)
- `name` / `label` / `text` / `value` / `placeholder`: Accessible names and visible text strings
- `application` / `window` / `container`: Contextual scopes
- `bounds`: Geometric bounding box `{x, y, width, height}`
- `enabled`, `visible`, `selected`, `focused`, `clickable`, `editable`: Interactive flags
- `source`: Perception source (`ACCESSIBILITY`, `DOM`, `APPLICATION_API`, `OCR`, `VISUAL`, `VLM`)
- `confidence`: Perception confidence score (0.0 to 1.0)
- `timestamp`: Creation timestamp

## Screen Semantic Snapshot (`ScreenSemanticSnapshot`)

Stores the active state of an application or web page:
- `application`, `window`, `url`
- `elements`: List of all `UIElement` items
- `regions`: Groupings for `header`, `sidebar`, `main`, `toolbar`, `dialog`, `table`, `form`
- `dialogs`, `forms`, `tables`
- `loading_state`: Boolean indicating active loading indicators
- `visible_text`: Concatenated text content
