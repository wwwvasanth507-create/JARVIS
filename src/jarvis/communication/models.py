"""
Data models for Universal Communication Subsystem in JARVIS.
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class CommunicationChannelType(str, Enum):
    EMAIL = "EMAIL"
    DESKTOP_MAIL = "DESKTOP_MAIL"
    WEBMAIL = "WEBMAIL"
    MESSAGING = "MESSAGING"


class ContactRecord(BaseModel):
    """Model representing a resolved contact."""
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    organization: Optional[str] = None
    notes: Optional[str] = None
    confidence: float = 1.0


class EmailMessage(BaseModel):
    """Structured Email Message Draft / Payload."""
    message_id: str
    recipient_name: str
    recipient_email: str
    subject: str
    body: str
    attachments: List[str] = Field(default_factory=list)
    channel: CommunicationChannelType = CommunicationChannelType.EMAIL
    status: str = "DRAFT"  # DRAFT, PREVIEWED, DISPATCHED, VERIFIED, FAILED
    requires_approval: bool = True
    created_at: float = Field(default_factory=dict)


class CommunicationResult(BaseModel):
    """Result emitted by communication channel execution."""
    success: bool
    message_id: Optional[str] = None
    recipient: str
    channel: str
    status: str
    error: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
