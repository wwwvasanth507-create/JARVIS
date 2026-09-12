"""
JARVIS Universal Communication Subsystem.
"""

from jarvis.communication.models import EmailMessage, ContactRecord, CommunicationResult, CommunicationChannelType
from jarvis.communication.contacts import ContactResolver
from jarvis.communication.composer import MessageComposer, SendPreview
from jarvis.communication.email_channel import EmailChannel
from jarvis.communication.verifier import CommunicationVerifier
from jarvis.communication.manager import CommunicationManager

__all__ = [
    "EmailMessage",
    "ContactRecord",
    "CommunicationResult",
    "CommunicationChannelType",
    "ContactResolver",
    "MessageComposer",
    "SendPreview",
    "EmailChannel",
    "CommunicationVerifier",
    "CommunicationManager",
]
