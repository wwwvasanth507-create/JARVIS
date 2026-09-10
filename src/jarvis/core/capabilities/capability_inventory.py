"""
Runtime Capability Inventory for JARVIS.

Tracks machine-readable metadata, risk tiers, availability, latency, verification,
and rollback methods for all JARVIS tools and subsystems across platforms.
"""

from enum import Enum
import platform
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from jarvis.security.permissions import PermissionCategory, RiskLevel

logger = logging.getLogger(__name__)


class CapabilityCategory(str, Enum):
    APPLICATION = "APPLICATION"
    COMPUTER = "COMPUTER"
    BROWSER = "BROWSER"
    FILESYSTEM = "FILESYSTEM"
    DOCUMENT = "DOCUMENT"
    SHELL = "SHELL"
    VOICE = "VOICE"
    VISION = "VISION"
    MEMORY = "MEMORY"
    SCHEDULER = "SCHEDULER"
    NOTIFICATION = "NOTIFICATION"
    SYSTEM = "SYSTEM"


class CapabilityDescriptor(BaseModel):
    id: str
    name: str
    category: CapabilityCategory
    platform_support: List[str] = Field(default_factory=lambda: ["Windows", "Linux", "Darwin"])
    dependencies: List[str] = Field(default_factory=list)
    risk_level: RiskLevel = RiskLevel.LOW
    permission_category: PermissionCategory = PermissionCategory.SYSTEM_CONTROL
    availability: bool = True
    latency_ms: float = 10.0
    verification_method: str = "state_check"
    rollback_method: Optional[str] = None
    allow_background: bool = True
    require_confirmation: bool = False


class CapabilityInventory:
    """Registry and manager for machine-readable runtime capability metadata."""

    _instance: Optional["CapabilityInventory"] = None

    def __init__(self):
        self._capabilities: Dict[str, CapabilityDescriptor] = {}
        self._register_default_capabilities()

    @classmethod
    def get_instance(cls) -> "CapabilityInventory":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register(self, cap: CapabilityDescriptor) -> None:
        self._capabilities[cap.id] = cap

    def get(self, capability_id: str) -> Optional[CapabilityDescriptor]:
        return self._capabilities.get(capability_id)

    def list_capabilities(self, category: Optional[CapabilityCategory] = None) -> List[CapabilityDescriptor]:
        if category is None:
            return list(self._capabilities.values())
        return [c for c in self._capabilities.values() if c.category == category]

    def _register_default_capabilities(self) -> None:
        # Application
        self.register(CapabilityDescriptor(
            id="application.open",
            name="Open Desktop Application",
            category=CapabilityCategory.APPLICATION,
            risk_level=RiskLevel.MEDIUM,
            permission_category=PermissionCategory.APPLICATION_CONTROL,
            verification_method="process_running_check",
            rollback_method="application.close"
        ))

        # Filesystem
        self.register(CapabilityDescriptor(
            id="filesystem.write_file",
            name="Write File",
            category=CapabilityCategory.FILESYSTEM,
            risk_level=RiskLevel.MEDIUM,
            permission_category=PermissionCategory.WRITE_FILES,
            verification_method="file_exists_and_size",
            rollback_method="file.backup_restore"
        ))
        self.register(CapabilityDescriptor(
            id="filesystem.delete",
            name="Delete File",
            category=CapabilityCategory.FILESYSTEM,
            risk_level=RiskLevel.HIGH,
            permission_category=PermissionCategory.DELETE_FILES,
            require_confirmation=True,
            verification_method="file_not_exists"
        ))

        # Browser
        self.register(CapabilityDescriptor(
            id="browser.search",
            name="Web Search",
            category=CapabilityCategory.BROWSER,
            risk_level=RiskLevel.LOW,
            permission_category=PermissionCategory.BROWSER_CONTROL,
            verification_method="results_non_empty"
        ))

        # Computer & Clipboard
        self.register(CapabilityDescriptor(
            id="computer.read_clipboard",
            name="Read Clipboard",
            category=CapabilityCategory.COMPUTER,
            risk_level=RiskLevel.LOW,
            permission_category=PermissionCategory.COMPUTER_CONTROL,
            verification_method="text_returned"
        ))
        self.register(CapabilityDescriptor(
            id="computer.write_clipboard",
            name="Write Clipboard",
            category=CapabilityCategory.COMPUTER,
            risk_level=RiskLevel.LOW,
            permission_category=PermissionCategory.COMPUTER_CONTROL,
            verification_method="clipboard_matches"
        ))

        # Notification & Scheduler
        self.register(CapabilityDescriptor(
            id="notification.dispatch",
            name="Dispatch Notification",
            category=CapabilityCategory.NOTIFICATION,
            risk_level=RiskLevel.LOW,
            permission_category=PermissionCategory.SYSTEM_CONTROL
        ))
        self.register(CapabilityDescriptor(
            id="scheduler.create",
            name="Schedule Recurring Task",
            category=CapabilityCategory.SCHEDULER,
            risk_level=RiskLevel.MEDIUM,
            permission_category=PermissionCategory.SYSTEM_CONTROL,
            rollback_method="scheduler.cancel"
        ))
