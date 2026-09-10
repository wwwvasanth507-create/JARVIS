"""
Structured application data models, state objects, and health representations for JARVIS.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, model_validator


class ApplicationInfo(BaseModel):
    name: str
    display_name: str = ""
    category: str = "utilities"
    aliases: List[str] = Field(default_factory=list)
    executable: str
    executable_path: Optional[str] = None
    common_paths: List[str] = Field(default_factory=list)
    platform: str = "win32"
    startup_timeout: int = 15

    @model_validator(mode="before")
    @classmethod
    def populate_display_name(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if not data.get("display_name"):
                data["display_name"] = data.get("name", "")
        return data


class ApplicationState(BaseModel):
    name: str
    display_name: str = ""
    running: bool = False
    pids: List[int] = Field(default_factory=list)
    launch_time: Optional[str] = None
    window_count: int = 0
    active_window_title: Optional[str] = None
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    status: str = "stopped"  # running, stopped, starting, unresponsive

    @property
    def is_running(self) -> bool:
        return self.running

    def model_dump(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        d = super().model_dump(*args, **kwargs)
        d["is_running"] = self.running
        return d


class ApplicationHealth(BaseModel):
    name: str
    running: bool
    responsive: bool
    window_count: int
    pids: List[int]
    status: str
    last_checked: str


class ApplicationStartupItem(BaseModel):
    name: str
    executable_path: str
    location: str  # registry, startup_folder, systemd, launchd
    enabled: bool = True


class LaunchResult(BaseModel):
    success: bool
    application: str
    pid: Optional[int] = None
    status: str
    verified: bool
    message: str
    data: Optional[Dict[str, Any]] = None


class CloseResult(BaseModel):
    success: bool
    application: str
    status: str
    graceful: bool
    has_unsaved_work: bool = False
    verified: bool
    message: str
    data: Optional[Dict[str, Any]] = None
