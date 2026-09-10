# Document Security & Privacy Policy

## Prompt Injection Defense
- Document text is ALWAYS treated as **untrusted DOCUMENT CONTENT data**.
- Text is scanned for injection phrases ("Ignore previous instructions", "system override") and automatically neutralized.
- Content is wrapped in `<UNTRUSTED_DOCUMENT_CONTENT doc_id="...">` tags before being passed to LLM or tool orchestrators.
- Instructions found inside documents can NEVER execute system tools or override user permissions.

## Privacy & Redaction
- Full document contents are never logged to persistent logs.
- Sensitive information (SSNs, API keys, passwords, emails, credit cards) is redacted via `DocumentPrivacyManager`.
