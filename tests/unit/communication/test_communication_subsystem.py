"""
Unit tests for JARVIS Universal Communication Subsystem and Tools.
"""

import pytest
from jarvis.communication.models import EmailMessage, ContactRecord, CommunicationResult
from jarvis.communication.contacts import ContactResolver
from jarvis.communication.composer import MessageComposer, SendPreview
from jarvis.communication.email_channel import EmailChannel
from jarvis.communication.verifier import CommunicationVerifier
from jarvis.communication.manager import CommunicationManager
from jarvis.tools.communication_tools import FindContactTool, ComposeEmailTool, PreviewEmailTool, SendEmailTool, VerifySentTool


def test_01_contact_resolver():
    resolver = ContactResolver()
    candidates = resolver.resolve_contact("Vasanth")
    assert len(candidates) >= 1
    assert "vasanth" in candidates[0].email.lower()

    single_res = resolver.get_single_recipient("Vasanth")
    assert single_res["contact"] is not None
    assert single_res["ambiguous"] is False


def test_02_message_composer_and_preview():
    composer = MessageComposer()
    contact = ContactRecord(name="Vasanth", email="vasanth@local.computer")
    draft = composer.compose_email(
        recipient=contact,
        subject="Meeting Postponed",
        body="The meeting is moved to 4 PM."
    )
    assert draft.message_id is not None
    assert draft.recipient_email == "vasanth@local.computer"

    preview_str = SendPreview.render_preview(draft)
    assert "OUTGOING MESSAGE PREVIEW" in preview_str
    assert "vasanth@local.computer" in preview_str


def test_03_communication_manager_and_email_channel():
    mgr = CommunicationManager.get_instance()
    
    # 1. Find Contact
    c_res = mgr.find_contact("Vasanth")
    assert c_res["contact"] is not None

    # 2. Compose Email
    draft = mgr.compose_email("Vasanth", "Status Update", "All systems operational.")
    assert draft.message_id is not None

    # 3. Preview Email
    preview_str = mgr.preview_email(draft.message_id)
    assert "Status Update" in preview_str

    # 4. Send Email (with force_approve)
    send_res = mgr.send_email(draft.message_id, force_approve=True)
    assert send_res.success is True

    # 5. Verify Sent
    v_res = mgr.verify_sent("Vasanth")
    assert v_res["verified"] is True


def test_04_communication_tools():
    find_tool = FindContactTool()
    compose_tool = ComposeEmailTool()
    preview_tool = PreviewEmailTool()
    send_tool = SendEmailTool()
    verify_tool = VerifySentTool()

    r1 = find_tool.execute(query="Vasanth")
    assert r1.success is True

    r2 = compose_tool.execute(recipient="Vasanth", subject="Test Subject", content="Test Content")
    assert r2.success is True
    draft_id = r2.data["draft_id"]

    r3 = preview_tool.execute(draft_id=draft_id)
    assert r3.success is True
    assert "Test Subject" in r3.data["preview"]

    r4 = send_tool.execute(draft_id=draft_id, force_approve=True)
    assert r4.success is True

    r5 = verify_tool.execute(recipient="Vasanth")
    assert r5.success is True
