# Semantic Computer Interaction Architecture

JARVIS integrates a unified multi-layer perception system and structured interaction engine (`SemanticComputerInteractor`) to provide reliable desktop and web UI automation.

## Core Operations

`SemanticComputerInteractor` exposes high-level semantic methods:
- `find_element(query: TargetQuery)`
- `click_element(query: TargetQuery)`
- `double_click_element(query: TargetQuery)`
- `right_click_element(query: TargetQuery)`
- `type_into_element(query: TargetQuery, text: str, sensitive: bool)`
- `select_element(query: TargetQuery, option: str)`
- `scroll_to_element(query: TargetQuery)`
- `focus_element(query: TargetQuery)`
- `read_element(query: TargetQuery)`
- `inspect_element(query: TargetQuery)`
- `wait_for_element(query: TargetQuery, timeout_sec: float)`
- `drag_element(query_src: TargetQuery, query_dst: TargetQuery)`
- `fill_form(form_data: Dict[str, Any], preview_first: bool)`
- `select_table_row(table_query: TargetQuery, text_in_row: str)`

## Perception Source Hierarchy

JARVIS prioritizes zero-cost reliable semantic APIs before falling back to optical or VLM perception:

1. **`ACCESSIBILITY` / `DOM`** (Confidence Weight: `0.98` / `0.95`)
2. **`APPLICATION_API`** (Confidence Weight: `0.90`)
3. **`OCR`** (Confidence Weight: `0.75`)
4. **`VISUAL`** (Confidence Weight: `0.60`)
5. **`VLM`** (Confidence Weight: `0.45`, optional local inference only)

## Target Leases & Action Safety

Before executing side-effect actions (clicks, key presses, form submissions), JARVIS acquires a `TargetLease` with TTL expiration and screen state hash validation to ensure the visual target remains fresh and unchanged.
