# Real-World Computer Agent Automation

## Governed Automation & Safety Rules
JARVIS supports natural-language automation creation (`"Every weekday at 9 AM, check my project folder for new reports and notify me"`, `"When the download finishes, move the PDF into my Reports folder"`).

### Controls:
- Every automation has an explicit owner (`Boss`), creation timestamp, condition, action, risk tier, permission requirements, and optional expiration date.
- No anonymous or unrestricted background automations are allowed.
- Bulk side-effects (e.g. mass moving >5 files) trigger a safety preview (`system.batch_preview`) and explicit confirmation requirement.
