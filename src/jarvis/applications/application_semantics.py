"""
Application Semantic State & Family Adapters for JARVIS.

Provides high-level semantic observations (busy/idle, modal_present, document_open,
unsaved_changes, ready) for desktop application families (Browsers, File Explorers,
Text Editors, Terminals, PDF Viewers, Office Editors).
"""

from enum import Enum
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ApplicationFamily(str, Enum):
    WEB_BROWSER = "WEB_BROWSER"
    FILE_EXPLORER = "FILE_EXPLORER"
    TEXT_EDITOR = "TEXT_EDITOR"
    TERMINAL = "TERMINAL"
    PDF_VIEWER = "PDF_VIEWER"
    OFFICE_EDITOR = "OFFICE_EDITOR"
    GENERIC = "GENERIC"


class ApplicationSemanticState(BaseModel):
    application_id: str
    family: ApplicationFamily = ApplicationFamily.GENERIC
    is_running: bool = True
    is_foreground: bool = False
    is_busy: bool = False
    modal_present: bool = False
    document_open: bool = False
    open_document_name: Optional[str] = None
    has_unsaved_changes: bool = False
    ready_status: str = "READY"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BaseApplicationSemanticAdapter:
    """Base class for generic application family semantic adapters."""

    def observe_semantics(self, app_name: str, window_title: Optional[str] = None) -> ApplicationSemanticState:
        title = (window_title or "").lower()
        has_unsaved = "*" in title or "unsaved" in title
        doc_open = len(title) > 0 and "blank" not in title

        return ApplicationSemanticState(
            application_id=app_name,
            family=self.infer_family(app_name),
            is_running=True,
            is_foreground=True,
            is_busy=False,
            modal_present="dialog" in title or "confirm" in title,
            document_open=doc_open,
            open_document_name=window_title,
            has_unsaved_changes=has_unsaved,
            ready_status="READY"
        )

    def infer_family(self, app_name: str) -> ApplicationFamily:
        name = app_name.lower()
        if any(b in name for b in ("chrome", "firefox", "edge", "browser")):
            return ApplicationFamily.WEB_BROWSER
        if any(e in name for e in ("explorer", "finder", "files")):
            return ApplicationFamily.FILE_EXPLORER
        if any(t in name for t in ("notepad", "vscode", "code", "sublime", "editor")):
            return ApplicationFamily.TEXT_EDITOR
        if any(sh in name for sh in ("cmd", "powershell", "terminal", "bash")):
            return ApplicationFamily.TERMINAL
        if any(p in name for p in ("acrobat", "pdf", "evince")):
            return ApplicationFamily.PDF_VIEWER
        if any(o in name for o in ("word", "excel", "office", "writer")):
            return ApplicationFamily.OFFICE_EDITOR
        return ApplicationFamily.GENERIC
