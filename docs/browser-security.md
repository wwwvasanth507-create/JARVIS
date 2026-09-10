# JARVIS Browser Security & Safety Policy

## Security Controls
1. **URL Validation**: Rejects unsupported protocols (`javascript:`, `data:`, executable custom schemes).
2. **Download Protection**: Downloaded files are saved to `data/downloads/` as untrusted files. Executables are never automatically executed.
3. **Upload Protection**: File uploads restrict sensitive file extensions (`.env`, `.key`, `.pem`, `shadow`, etc.) without explicit authorization.
4. **Sensitive Actions & Risk Evaluation**: Financial transactions, password changes, account deletions, and purchases raise `HIGH` or `CRITICAL` risk requiring confirmation.
5. **Login & Credentials Handling**: Credentials are never scraped or logged. Passwords, auth tokens, and session cookies are never exposed in logs or model context.
6. **CAPTCHA / Anti-Bot Detection**: If a CAPTCHA or anti-bot challenge is detected, JARVIS returns `HUMAN_INTERVENTION_REQUIRED` without attempting automated bypass.
