"""
Communication & Email Tools for JARVIS.
Provides structured tool interfaces for contact resolution, message composition,
payload previewing, message dispatching, and sent state verification.
"""

from typing import Any, Dict
from jarvis.tools.base import BaseTool, ToolMetadata, ToolResult
from jarvis.security.permissions import PermissionCategory, RiskLevel
from jarvis.communication.manager import CommunicationManager


class FindContactTool(BaseTool):
    def __init__(self):
        super().__init__(
            ToolMetadata(
                name="communication.find_contact",
                description="Finds recipient contact information and email address candidates.",
                input_schema={
                    "type": "object",
                    "properties": {"query": {"type": "string"}},
                    "required": ["query"]
                },
                permission_requirement=PermissionCategory.READ_FILES,
                risk_level=RiskLevel.LOW
            )
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        mgr = CommunicationManager.get_instance()
        res = mgr.find_contact(kwargs["query"])
        contact = res.get("contact")
        return ToolResult(
            success=True,
            data={
                "contact": contact.__dict__ if contact else None,
                "ambiguous": res.get("ambiguous", False),
                "message": f"Resolved contact for '{kwargs['query']}': {contact.email if contact else 'None'}"
            }
        )

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class ComposeEmailTool(BaseTool):
    def __init__(self):
        super().__init__(
            ToolMetadata(
                name="communication.compose_email",
                description="Composes a structured email draft.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "recipient": {"type": "string"},
                        "subject": {"type": "string"},
                        "content": {"type": "string"}
                    },
                    "required": ["recipient", "subject", "content"]
                },
                permission_requirement=PermissionCategory.NETWORK_ACCESS,
                risk_level=RiskLevel.LOW
            )
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        mgr = CommunicationManager.get_instance()
        draft = mgr.compose_email(
            recipient_query=kwargs["recipient"],
            subject=kwargs["subject"],
            body=kwargs["content"]
        )
        return ToolResult(
            success=True,
            data={
                "draft_id": draft.message_id,
                "recipient": draft.recipient_email,
                "subject": draft.subject,
                "message": f"Composed email draft '{draft.message_id}' to {draft.recipient_email}"
            }
        )

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class PreviewEmailTool(BaseTool):
    def __init__(self):
        super().__init__(
            ToolMetadata(
                name="communication.preview_email",
                description="Renders exact outgoing email payload preview for Boss inspection.",
                input_schema={
                    "type": "object",
                    "properties": {"draft_id": {"type": "string", "default": "latest"}}
                },
                permission_requirement=PermissionCategory.SYSTEM_CONTROL,
                risk_level=RiskLevel.LOW
            )
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        mgr = CommunicationManager.get_instance()
        preview_str = mgr.preview_email(kwargs.get("draft_id", "latest"))
        return ToolResult(
            success=True,
            data={"preview": preview_str, "message": preview_str}
        )

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class SendEmailTool(BaseTool):
    def __init__(self):
        super().__init__(
            ToolMetadata(
                name="communication.send_email",
                description="Dispatches outgoing email message.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "draft_id": {"type": "string", "default": "latest"},
                        "force_approve": {"type": "boolean", "default": False}
                    }
                },
                permission_requirement=PermissionCategory.NETWORK_ACCESS,
                risk_level=RiskLevel.HIGH
            )
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        mgr = CommunicationManager.get_instance()
        res = mgr.send_email(
            draft_id=kwargs.get("draft_id", "latest"),
            force_approve=kwargs.get("force_approve", False)
        )
        return ToolResult(
            success=res.success,
            data={
                "message_id": res.message_id,
                "recipient": res.recipient,
                "status": res.status,
                "message": f"Email dispatch result for '{res.recipient}': {res.status}"
            },
            error=res.error
        )

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class VerifySentTool(BaseTool):
    def __init__(self):
        super().__init__(
            ToolMetadata(
                name="communication.verify_sent",
                description="Verifies that an email was verifiably sent.",
                input_schema={
                    "type": "object",
                    "properties": {"recipient": {"type": "string"}},
                    "required": ["recipient"]
                },
                permission_requirement=PermissionCategory.SYSTEM_CONTROL,
                risk_level=RiskLevel.LOW
            )
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        mgr = CommunicationManager.get_instance()
        v_res = mgr.verify_sent(kwargs["recipient"])
        return ToolResult(
            success=v_res["verified"],
            data={
                "verified": v_res["verified"],
                "target": v_res["target"],
                "evidence": v_res["evidence"],
                "message": f"Sent verification for '{kwargs['recipient']}': {v_res['verified']}"
            }
        )

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


COMMUNICATION_TOOLS = [
    FindContactTool(),
    ComposeEmailTool(),
    PreviewEmailTool(),
    SendEmailTool(),
    VerifySentTool(),
]
