"""
Modal, Alert, and Security Dialog Manager for JARVIS.
"""

from enum import Enum
import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from jarvis.computer.vision.ui_element import UIElement

logger = logging.getLogger(__name__)


class DialogSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    SECURITY = "SECURITY"


class DialogType(str, Enum):
    ALERT = "ALERT"
    CONFIRMATION = "CONFIRMATION"
    LOGIN = "LOGIN"
    PERMISSION = "PERMISSION"
    ERROR = "ERROR"
    INFORMATION = "INFORMATION"


class UIDialog(BaseModel):
    """
    Represents a desktop or web modal dialog.
    """
    dialog_id: str
    title: str = "Dialog"
    message: str = ""
    dialog_type: DialogType = DialogType.INFORMATION
    severity: DialogSeverity = DialogSeverity.INFO
    buttons: List[str] = Field(default_factory=list)  # e.g. ["OK", "Cancel"]
    is_blocking: bool = True
    is_security_prompt: bool = False
    dialog_element: Optional[UIElement] = None


class DialogManager:
    """
    Detects, classifies, and governs interaction with modal dialogs and popups.
    Ensures security and permission prompts are NEVER auto-approved without user consent.
    """

    @classmethod
    def classify_dialog(cls, title: str, message: str, buttons: List[str]) -> UIDialog:
        t_lower = title.lower()
        m_lower = message.lower()

        is_sec = any(kw in t_lower or kw in m_lower for kw in ("permission", "security", "admin", "authorize", "grant", "sudo", "credential"))
        if is_sec:
            dtype = DialogType.PERMISSION
            sev = DialogSeverity.SECURITY
        elif any(kw in t_lower or kw in m_lower for kw in ("error", "fail", "exception", "fatal")):
            dtype = DialogType.ERROR
            sev = DialogSeverity.ERROR
        elif any(kw in t_lower or kw in m_lower for kw in ("warning", "confirm", "are you sure")):
            dtype = DialogType.CONFIRMATION
            sev = DialogSeverity.WARNING
        elif any(kw in t_lower or kw in m_lower for kw in ("login", "sign in", "password")):
            dtype = DialogType.LOGIN
            sev = DialogSeverity.SECURITY
            is_sec = True
        else:
            dtype = DialogType.INFORMATION
            sev = DialogSeverity.INFO

        return UIDialog(
            dialog_id=f"dlg_{title[:10]}",
            title=title,
            message=message,
            dialog_type=dtype,
            severity=sev,
            buttons=buttons or ["OK"],
            is_blocking=True,
            is_security_prompt=is_sec,
        )

    @classmethod
    def can_auto_dismiss(cls, dialog: UIDialog) -> bool:
        """
        Determines if a dialog can be safely dismissed without explicit user confirmation.
        Security and permission prompts MUST NEVER be auto-dismissed/approved.
        """
        if dialog.is_security_prompt or dialog.severity == DialogSeverity.SECURITY:
            logger.warning(f"Dialog '{dialog.title}' is a security prompt. Auto-dismiss blocked.")
            return False
        if dialog.dialog_type in (DialogType.PERMISSION, DialogType.LOGIN):
            return False
        return True
