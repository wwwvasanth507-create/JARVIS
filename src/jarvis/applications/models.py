"""
Application Data Models for JARVIS.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class ApplicationEntry(BaseModel):
    name: str
    aliases: List[str] = Field(default_factory=list)
    executable: str
    common_paths: List[str] = Field(default_factory=list)


class ApplicationStatus(BaseModel):
    name: str
    executable: str
    is_running: bool = False
    process_ids: List[int] = Field(default_factory=list)
    resolved_path: Optional[str] = None
