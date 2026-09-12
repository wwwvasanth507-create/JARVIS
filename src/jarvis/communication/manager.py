"""
Central Communication Manager Facade for JARVIS.
Integrates ContactResolver, MessageComposer, SendPreview, EmailChannel, and CommunicationVerifier.
"""

import logging
from typing import Dict, Any, List, Optional

from jarvis.communication.models import EmailMessage, ContactRecord, CommunicationResult
from jarvis.communication.contacts import ContactResolver
from jarvis.communication.composer import MessageComposer, SendPreview
from jarvis.communication.email_channel import EmailChannel
from jarvis.communication.verifier import CommunicationVerifier

logger = logging.getLogger("jarvis.communication.manager")


class CommunicationManager:
    """Central unified manager for local communication, contact resolution, and email workflows."""

    _instance: Optional["CommunicationManager"] = None

    @classmethod
    def get_instance(cls) -> "CommunicationManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.contacts = ContactResolver()
        self.composer = MessageComposer()
        self.email_channel = EmailChannel()
        self.verifier = CommunicationVerifier(self.email_channel)

    def find_contact(self, query: str) -> Dict[str, Any]:
        """Resolves recipient contact candidates."""
        return self.contacts.get_single_recipient(query)

    def compose_email(self, recipient_query: str, subject: str, body: str) -> EmailMessage:
        """Resolves contact and composes structured email draft."""
        rec_res = self.find_contact(recipient_query)
        contact = rec_res.get("contact") or ContactRecord(name=recipient_query, email=f"{recipient_query.lower()}@local.computer")
        return self.composer.compose_email(recipient=contact, subject=subject, body=body)

    def preview_email(self, draft_id: str = "latest") -> str:
        """Renders exact outgoing message preview for Boss inspection."""
        draft = self.composer.get_draft(draft_id)
        if not draft:
            return "Error: No draft message found to preview."
        return SendPreview.render_preview(draft)

    def send_email(self, draft_id: str = "latest", force_approve: bool = False) -> CommunicationResult:
        """Sends email draft after verifying approval requirements."""
        draft = self.composer.get_draft(draft_id)
        if not draft:
            return CommunicationResult(
                success=False,
                recipient="unknown",
                channel="EMAIL",
                status="FAILED",
                error="No draft email found to send."
            )
        if force_approve:
            draft.status = "APPROVED"

        return self.email_channel.send(draft)

    def verify_sent(self, recipient_or_id: str) -> Dict[str, Any]:
        """Verifies sent email state."""
        return self.verifier.verify_sent(recipient_or_id)
