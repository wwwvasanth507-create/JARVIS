# Universal Email & Communication Guide (Prompt 026)

## Overview
JARVIS includes a provider-agnostic, governed **Universal Communication Subsystem** (`src/jarvis/communication/`). It provides contact resolution from local memory and context, natural-language message drafting, exact outgoing payload previews, safety approval enforcement, email dispatch, and sent state verification.

---

## Subsystem Architecture

```
[User Natural Language Request]
             │
             ▼
      ContactResolver ──────> Searches Memory & Known Contacts
             │
             ▼
      MessageComposer ──────> Generates Draft & Structured Content
             │
             ▼
     CommunicationManager ──> Renders Exact Outgoing Preview Payload
             │
             ▼
   [Boss Approval Gate]  ───> If High Risk, Requires Explicit Confirmation
             │
             ▼
        EmailChannel ───────> Dispatches Message & Verifies Sent Evidence
```

---

## Core Capabilities

### 1. Contact Resolution (`ContactResolver`)
- Resolves recipient names against local contact databases and semantic memory facts.
- Safely detects ambiguous contacts (e.g. "Vasanth Kumar" vs "Vasanth Rao") and presents candidates without guessing.

### 2. Message Composition & Draft Preview (`MessageComposer`)
- Structures message intent, recipient, subject, body, and attachments.
- Renders an explicit **JARVIS Outgoing Message Preview (HIGH RISK)** payload for Boss inspection before dispatch.

### 3. Outgoing Message Preview Format
```
==================================================
    JARVIS OUTGOING MESSAGE PREVIEW (HIGH RISK)   
==================================================
  TO          : Vasanth <vasanth@local.computer>
  SUBJECT     : Meeting Reschedule
  CONTENT     : The client meeting has been postponed to 4 PM.
  ATTACHMENTS : None
  CHANNEL     : EMAIL
  STATUS      : DRAFT (Requires Boss Approval: True)
==================================================
```

### 4. Registered Communication Tools
- `communication.find_contact`: Search/resolve contacts.
- `communication.compose_email`: Create email drafts.
- `communication.preview_email`: Render exact message preview payload.
- `communication.send_email`: Dispatch email (governed by confirmation policy).
- `communication.verify_sent`: Verify sent message evidence.

---

## Python Usage Example

```python
from jarvis.communication.manager import CommunicationManager
from jarvis.communication.contacts import ContactResolver

# 1. Resolve Contact
contact = ContactResolver.resolve("Vasanth")

# 2. Compose Email Draft
comm_mgr = CommunicationManager()
draft = comm_mgr.compose_email(
    recipient_query="Vasanth",
    subject="Project Status Update",
    body="The quarterly deliverables are ready for review."
)

# 3. Preview Message Payload
preview_text = comm_mgr.preview_email(draft.message_id)
print(preview_text)

# 4. Dispatch Email (with force_approve in automated harnesses)
result = comm_mgr.send_email(draft.message_id, force_approve=True)
print("Dispatch Result:", result.status)

# 5. Verify Sent State
verification = comm_mgr.verify_sent(draft.message_id)
print("Verified:", verification["verified"])
```
