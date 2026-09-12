"""
Message Composer & Exact Payload Preview Renderer for JARVIS Communication Subsystem.
Builds structured EmailMessage objects and formats clear outgoing previews for Boss review.
"""

import time
import uuid
import logging
from typing import Dict, Any, List, Optional

from jarvis.communication.models import EmailMessage, ContactRecord, CommunicationChannelType

logger = logging.getLogger("jarvis.communication.composer")


class MessageComposer:
    """Creates structured email and message payloads."""

    def __init__(self):
        self._drafts: Dict[str, EmailMessage] = {}

    def compose_email(
        self,
        recipient: ContactRecord,
        subject: str,
        body: str,
        attachments: Optional[List[str]] = None,
        channel: CommunicationChannelType = CommunicationChannelType.EMAIL,
        requires_approval: bool = True
    ) -> EmailMessage:
        msg_id = f"msg_{uuid.uuid4().hex[:8]}"
        email_msg = EmailMessage(
            message_id=msg_id,
            recipient_name=recipient.name,
            recipient_email=recipient.email or f"{recipient.name.lower()}@local.computer",
            subject=subject,
            body=body,
            attachments=attachments or [],
            channel=channel,
            status="DRAFT",
            requires_approval=requires_approval
        )
        self._drafts[msg_id] = email_msg
        logger.info(f"MessageComposer created email draft '{msg_id}' to {email_msg.recipient_email}")
        return email_msg

    def get_draft(self, draft_id: str) -> Optional[EmailMessage]:
        if draft_id == "latest" and self._drafts:
            return list(self._drafts.values())[-1]
        return self._drafts.get(draft_id)


class SendPreview:
    """Renders formatted visual outgoing payload previews for Boss confirmation."""

    @classmethod
    def render_preview(cls, message: EmailMessage) -> str:
        attach_str = ", ".join(message.attachments) if message.attachments else "None"
        preview_text = (
            "==================================================\n"
            "    JARVIS OUTGOING MESSAGE PREVIEW (HIGH RISK)   \n"
            "==================================================\n"
            f"  TO          : {message.recipient_name} <{message.recipient_email}>\n"
            f"  SUBJECT     : {message.subject}\n"
            f"  CONTENT     : {message.body}\n"
            f"  ATTACHMENTS : {attach_str}\n"
            f"  CHANNEL     : {message.channel.value}\n"
            f"  STATUS      : {message.status} (Requires Boss Approval: {message.requires_approval})\n"
            "=================================================="
        )
        return preview_text
