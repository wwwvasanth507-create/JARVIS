"""
First-Run Onboarding Flow for JARVIS Personal AI Assistant.
"""

import logging
from typing import Dict, Any, Optional
from jarvis.memory.profile import WorkspaceProfileManager, WorkspaceProfile

logger = logging.getLogger(__name__)


class OnboardingManager:
    """
    Manages optional first-run onboarding sequence for setting user name,
    language preferences (English/Tamil/Tanglish), voice, and default directories.
    """

    def __init__(self):
        self.profile_mgr = WorkspaceProfileManager.get_instance()

    def is_onboarding_needed(self) -> bool:
        return not self.profile_mgr.profile.onboarding_completed

    def run_onboarding(self, config_inputs: Optional[Dict[str, Any]] = None) -> WorkspaceProfile:
        """
        Executes onboarding configuration. All options are optional and defaults apply gracefully.
        """
        inputs = config_inputs or {}
        profile = self.profile_mgr.profile

        profile.user_name = inputs.get("user_name") or profile.user_name
        profile.language_preference = inputs.get("language") or profile.language_preference
        profile.preferred_voice = inputs.get("voice") or profile.preferred_voice
        profile.preferred_browser = inputs.get("browser") or profile.preferred_browser
        profile.default_workspace_dir = inputs.get("workspace_dir") or profile.default_workspace_dir
        profile.onboarding_completed = True

        self.profile_mgr.save_profile(profile)
        logger.info(f"Onboarding completed for {profile.user_name} (Language: {profile.language_preference})")
        return profile
