"""
Communication Verifier for JARVIS.
Verifies sent email state via sent log inspection, window state observation, or sent folder state.
"""

import logging
from typing import Dict, Any, Optional

from jarvis.communication.email_channel import EmailChannel

logger = logging.getLogger("jarvis.communication.verifier")


class CommunicationVerifier:
    """Verifies that an email or message was actually sent and recorded."""

    def __init__(self, email_channel: EmailChannel):
        self.email_channel = email_channel

    def verify_sent(self, recipient_or_id: str) -> Dict[str, Any]:
        verified = self.email_channel.is_sent(recipient_or_id)
        logger.info(f"CommunicationVerifier checking '{recipient_or_id}': verified={verified}")
        return {
            "verified": verified,
            "target": recipient_or_id,
            "evidence": "Sent log entry confirmed" if verified else "No sent record found"
        }
