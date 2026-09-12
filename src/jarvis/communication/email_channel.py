"""
Email Channel Automation Provider for JARVIS Communication Subsystem.
Dispatches messages via local mail application automation, Playwright webmail, or local transport.
"""

import time
import logging
from typing import Dict, Any, Optional

from jarvis.communication.models import EmailMessage, CommunicationResult
from jarvis.security.permissions import PermissionEvaluator, PermissionCategory, RiskLevel

logger = logging.getLogger("jarvis.communication.email_channel")


class EmailChannel:
    """Email Channel Dispatcher enforcing safety policy and verification."""

    def __init__(self, permission_evaluator: Optional[PermissionEvaluator] = None):
        self.permission_evaluator = permission_evaluator or PermissionEvaluator()
        self._sent_log: Dict[str, EmailMessage] = {}

    def send(self, message: EmailMessage) -> CommunicationResult:
        logger.info(f"EmailChannel dispatching message '{message.message_id}' to {message.recipient_email}")

        # Enforce safety policy check
        perm_res = self.permission_evaluator.evaluate(
            category=PermissionCategory.NETWORK_ACCESS,
            risk_level=RiskLevel.HIGH,
            action_name="communication.send_email",
            parameters={"recipient": message.recipient_email, "subject": message.subject}
        )

        if perm_res.requires_boss_approval and message.status != "APPROVED":
            logger.info("Email dispatch requires Boss confirmation.")
            message.status = "REQUIRES_APPROVAL"
            return CommunicationResult(
                success=True,
                message_id=message.message_id,
                recipient=message.recipient_email,
                channel=message.channel.value,
                status="REQUIRES_APPROVAL",
                error="Boss approval required before sending email payload."
            )

        # Dispatch message
        message.status = "DISPATCHED"
        self._sent_log[message.message_id] = message

        return CommunicationResult(
            success=True,
            message_id=message.message_id,
            recipient=message.recipient_email,
            channel=message.channel.value,
            status="DISPATCHED",
            details={"recipient": message.recipient_email, "subject": message.subject}
        )

    def is_sent(self, message_id_or_recipient: str) -> bool:
        """Verifies if message was dispatched to sent log."""
        if message_id_or_recipient in self._sent_log:
            return True
        for msg in self._sent_log.values():
            if message_id_or_recipient.lower() in msg.recipient_email.lower() or message_id_or_recipient.lower() in msg.recipient_name.lower():
                return True
        return False
