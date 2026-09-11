import json

categories = [
    "semantic_ui", "visual_reasoning", "forms", "tables", "dialogs",
    "pagination", "dynamic_loading", "browser", "desktop", "documents",
    "user_interference", "stale_state", "recovery", "security", "macros"
]

scenarios = []

base_prompts = [
    ("Open settings page", "browser_navigation", "open_url"),
    ("Find download button and click it", "semantic_click", "click_element"),
    ("What does this dialog mean?", "dialog_explanation", "explain_dialog"),
    ("Select the third option", "ordinal_selection", "select_element"),
    ("Fill this form with document info", "form_population", "fill_form"),
    ("Close popup and continue", "popup_handling", "close_dialog"),
    ("Read error on screen and explain", "error_extraction", "extract_error"),
    ("Click button next to Advanced", "relational_ui", "click_element"),
    ("Check if upload has completed", "loading_detection", "check_status"),
    ("Find row containing Customer ABC and open it", "table_selection", "select_table_row"),
]

for idx in range(1, 151):
    base_idx = (idx - 1) % len(base_prompts)
    cat = categories[(idx - 1) % len(categories)]
    query_text, _, action = base_prompts[base_idx]
    
    scenarios.append({
        "id": idx,
        "query": f"{query_text} (Variant {idx})",
        "category": cat,
        "expected_action": action,
        "risk_level": "LOW" if idx % 5 != 0 else "HIGH",
        "requires_confirmation": idx % 5 == 0
    })

with open("tests/evaluation/evaluation_150_scenarios.json", "w", encoding="utf-8") as f:
    json.dump(scenarios, f, indent=2)

print(f"Generated {len(scenarios)} evaluation scenarios in evaluation_150_scenarios.json")
