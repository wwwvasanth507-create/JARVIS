# Semantic User Macros & User Teaching Mode

JARVIS supports reusable user-taught automation workflows (`SemanticMacro`).

## Structure

- `macro_id`, `name`, `version`, `created_at`
- `steps`: List of `SemanticMacroStep` items storing semantic target queries (e.g. `button "Reports" inside "Navigation"`) rather than raw coordinate macros.
- `required_capabilities`, `risk_level`

## Safety & Validation

- Pre-execution validation verifies safety policies before running macro steps.
- Password and token inputs are redacted and prevented from being stored in macro steps.
