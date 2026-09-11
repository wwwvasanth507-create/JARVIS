# Form Understanding, Data Binding & Pre-Submission Preview

JARVIS models forms as structured entities with safe data binding capabilities.

## Form Structure (`Form` & `FormField`)

- Field labels, control types (`text`, `password`, `checkbox`, `radio`, `select`), values, and placeholders.
- Redaction of sensitive fields (passwords, tokens, payment data).

## Local Document -> Form Workflow

1. Read local document (PDF, TXT, JSON, DOCX) via `DocumentRegistry`.
2. Extract key-value field data.
3. Map document fields to form targets (`map_document_data`).
4. Generate pre-submission safety preview (`FormPreview`).
5. Populate form fields via `SemanticComputerInteractor`.
6. Enforce permission check for high-risk external submission.
7. Post-submission state verification.
