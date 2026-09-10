"""
Browser State Data Models and Results for JARVIS.
"""

import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class TabInfo(BaseModel):
    id: str
    url: str = ""
    title: str = ""
    is_active: bool = False


class BrowserState(BaseModel):
    running: bool = False
    current_url: str = ""
    current_title: str = ""
    active_tab_id: Optional[str] = None
    tabs: List[TabInfo] = Field(default_factory=list)
    timestamp: float = Field(default_factory=time.time)


class BrowserActionResult(BaseModel):
    success: bool
    status: str = "SUCCESS"  # SUCCESS, FAILED, TIMEOUT, DENIED, UNCERTAIN, AMBIGUOUS_TARGET, HUMAN_INTERVENTION_REQUIRED
    message: str = ""
    action: Optional[str] = None
    url: Optional[str] = None
    title: Optional[str] = None
    error: Optional[str] = None
    data: Optional[Any] = None
    details: Optional[Dict[str, Any]] = None
    duration_seconds: float = 0.0
    verified: bool = False


class SearchResult(BaseModel):
    title: str
    url: str
    snippet: str = ""
    position: int = 1
