"""
Personal Workspace Profile and Language Preference Manager for JARVIS.

Manages user profile preferences (Boss name, language: English/Tamil/Tanglish, voice, browser, default workspace).
Profile data is strictly local, editable, removable, and never transmitted externally.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

from jarvis.utils.paths import ResourcePathResolver

logger = logging.getLogger(__name__)


class WorkspaceProfile(BaseModel):
    user_name: str = "Boss"
    language_preference: str = "English"  # "English", "Tamil", "Tanglish"
    preferred_voice: str = "female_neutral"
    preferred_browser: str = "Chrome"
    default_workspace_dir: Optional[str] = None
    default_documents_dir: Optional[str] = None
    onboarding_completed: bool = False
    custom_preferences: Dict[str, Any] = Field(default_factory=dict)


class WorkspaceProfileManager:
    """
    Manages local WorkspaceProfile persistence and query resolution.
    """

    _instance: Optional["WorkspaceProfileManager"] = None

    def __init__(self, profile_path: Optional[Path] = None):
        self.profile_path = profile_path or (ResourcePathResolver.get_config_dir() / "user_profile.json")
        self.profile = self.load_profile()

    @classmethod
    def get_instance(cls) -> "WorkspaceProfileManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def load_profile(self) -> WorkspaceProfile:
        if self.profile_path.exists():
            try:
                with open(self.profile_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return WorkspaceProfile(**data)
            except Exception as e:
                logger.warning(f"Could not load user profile: {e}")
        return WorkspaceProfile()

    def save_profile(self, profile: Optional[WorkspaceProfile] = None) -> None:
        if profile:
            self.profile = profile
        self.profile_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.profile_path, "w", encoding="utf-8") as f:
            json.dump(self.profile.model_dump(), f, indent=2)
        logger.info(f"Saved WorkspaceProfile to {self.profile_path}")

    def update_language_preference(self, language: str) -> None:
        valid_langs = ("English", "Tamil", "Tanglish")
        if language in valid_langs:
            self.profile.language_preference = language
            self.save_profile()
            logger.info(f"Updated language preference to {language}")
