"""
Natural Language Task Interpreter for JARVIS General Reasoning.
Deconstructs arbitrary user requests into structured intent, primary domain,
recipient details, payload content, parameters, completion conditions, and safety flags.
"""

import re
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("jarvis.core.reasoning.interpreter")


class StructuredIntent(BaseModel):
    """Structured representation of interpreted user intent."""
    raw_query: str
    objective: str = "GENERAL_QUERY"
    primary_domain: str = "SYSTEM"  # COMMUNICATION, FILESYSTEM, DOCUMENT, BROWSER, COMPUTER, SYSTEM
    recipient: Optional[str] = None
    subject: Optional[str] = None
    content: Optional[str] = None
    target_app: Optional[str] = None
    target_path: Optional[str] = None
    target_url: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    completion_condition: str = "DEFAULT_SUCCESS"
    verification_required: bool = True
    requires_boss_approval: bool = False
    confidence: float = 0.90


class TaskInterpreter:
    """
    Interprets natural-language user requests into structured goals and intent models
    without hardcoded single-app heuristics.
    """

    @classmethod
    def interpret(cls, user_request: str) -> StructuredIntent:
        text = user_request.strip()
        text_lower = text.lower()

        intent = StructuredIntent(raw_query=text)

        # 1. Check Cross-Application Workflow Intent (PDF to Form, Download to Spreadsheet, Report to Email)
        if ("pdf" in text_lower or "report" in text_lower or "invoice" in text_lower or "download" in text_lower or "read " in text_lower) and \
           ("email" in text_lower or "mail" in text_lower or "form" in text_lower or "spreadsheet" in text_lower or "summary" in text_lower):
            intent.objective = "CROSS_APP_WORKFLOW"
            intent.primary_domain = "DOCUMENT"
            intent.completion_condition = "WORKFLOW_TRANSITION_VERIFIED"
            
            if "email" in text_lower or "mail" in text_lower:
                m_rec = re.search(r"(?:to|email|mail)\s+([A-Z][a-z0-9_\-\.\@]+)", text, re.IGNORECASE)
                if m_rec:
                    intent.recipient = m_rec.group(1).strip()
            
            return intent

        # 2. Check Communication Intent (Email / Mail / Contact)
        if any(kw in text_lower for kw in ("send mail", "send email", "email ", "mail to", "message to", "reply to email", "contact info", "find contact", "draft an email", "draft email")):
            intent.objective = "SEND_EMAIL"
            intent.primary_domain = "COMMUNICATION"
            intent.verification_required = True

            m_rec = re.search(r"\bto\s+([A-Za-z0-9_\-\.\@]+)", text, re.IGNORECASE)
            if not m_rec:
                m_rec = re.search(r"(?:email|mail|for)\s+([A-Z][a-z0-9_\-\.\@]+)", text, re.IGNORECASE)
            if m_rec:
                cand = m_rec.group(1).strip()
                if cand.lower() not in ("email", "mail", "a", "the", "info", "for"):
                    intent.recipient = cand

            m_content = re.search(r"(?:saying|about|content|message|that)\s+(.+)$", text, re.IGNORECASE)
            if m_content:
                intent.content = m_content.group(1).strip()

            if "find contact" in text_lower or "contact info" in text_lower:
                intent.requires_boss_approval = False
            else:
                intent.requires_boss_approval = True

            return intent

        # 3. Check Filesystem Operation Intent
        if any(kw in text_lower for kw in ("create file", "write file", "read file", "find file", "create folder", "list text files", "delete file")):
            intent.objective = "FILESYSTEM_OPERATION"
            intent.primary_domain = "FILESYSTEM"
            intent.completion_condition = "FILESYSTEM_STATE_VERIFIED"

            m_path = re.search(r"([A-Za-z]:[/\\][^\s]+|[A-Za-z0-9_/\-\.\\:]+\.[a-zA-Z0-9]+)", text)
            if m_path:
                intent.target_path = m_path.group(1).strip()

            m_content = re.search(r"(?:with\s+content|content)\s+(.+)$", text, re.IGNORECASE)
            if m_content:
                intent.content = m_content.group(1).strip()

            if "delete" in text_lower or "remove" in text_lower:
                intent.requires_boss_approval = True

            return intent

        # 4. Check Application Control Intent
        if any(kw in text_lower for kw in ("open app", "launch", "open notepad", "close notepad", "focus notepad", "open calculator")):
            intent.objective = "APPLICATION_CONTROL"
            intent.primary_domain = "COMPUTER"
            intent.completion_condition = "PROCESS_WINDOW_VERIFIED"

            m_app = re.search(r"(?:open|launch|focus|close)\s+([a-zA-Z0-9_\-\.]+)", text, re.IGNORECASE)
            if m_app:
                candidate = m_app.group(1).strip()
                if candidate.lower() not in ("app", "application", "the", "a", "file", "browser", "mail"):
                    intent.target_app = candidate

            return intent

        # 5. Check Browser Control Intent
        if any(kw in text_lower for kw in ("open browser", "navigate to", "search for", "open webpage", "http://", "https://")):
            intent.objective = "BROWSER_NAVIGATION"
            intent.primary_domain = "BROWSER"
            intent.completion_condition = "BROWSER_DOM_VERIFIED"

            m_url = re.search(r"(https?://[^\s]+|www\.[^\s]+|[a-zA-Z0-9_\-]+\.(?:com|org|net|io|gov))", text)
            if m_url:
                url_str = m_url.group(1).strip()
                intent.target_url = url_str if url_str.startswith("http") else f"https://{url_str}"

            return intent

        # 6. Fallback General Query / Task
        intent.objective = "GENERAL_QUERY"
        intent.primary_domain = "SYSTEM"
        intent.completion_condition = "RESPONSE_GENERATED"
        return intent
