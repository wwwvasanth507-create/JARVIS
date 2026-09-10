"""
Central Resource Arbitrator for JARVIS.

Governs leases and concurrency limits for Model, Browser, Vision, and Voice subsystems,
enforcing CPU-first memory safety and user interrupt priority.
"""

from enum import Enum
import time
import logging
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ResourceType(str, Enum):
    MODEL = "MODEL"
    BROWSER = "BROWSER"
    VISION = "VISION"
    VOICE = "VOICE"
    MICROPHONE = "MICROPHONE"


class ResourceLease(BaseModel):
    lease_id: str
    resource_type: ResourceType
    owner_task_id: str
    priority: int = 1  # 1 = Background, 2 = Normal, 3 = User Interrupt
    acquired_at: float = Field(default_factory=time.time)
    expires_at: float


class ResourceArbitrator:
    """Central Resource Arbitrator managing contention across subsystem resources."""

    _instance: Optional["ResourceArbitrator"] = None

    def __init__(self):
        self._active_leases: Dict[ResourceType, ResourceLease] = {}
        self._concurrency_limits: Dict[ResourceType, int] = {
            ResourceType.MODEL: 1,
            ResourceType.BROWSER: 2,
            ResourceType.VISION: 1,
            ResourceType.VOICE: 1,
            ResourceType.MICROPHONE: 1,
        }

    @classmethod
    def get_instance(cls) -> "ResourceArbitrator":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def acquire_resource(self, resource_type: ResourceType, owner_task_id: str, priority: int = 1, lease_sec: float = 60.0) -> Optional[ResourceLease]:
        now = time.time()
        existing = self._active_leases.get(resource_type)

        if existing and now < existing.expires_at:
            # Check if higher priority task preempts existing lease
            if priority > existing.priority:
                logger.info(f"ResourceArbitrator preempting lease on '{resource_type.value}' for higher priority task '{owner_task_id}' (P{priority} > P{existing.priority})")
            else:
                logger.warning(f"ResourceArbitrator denied resource '{resource_type.value}' to '{owner_task_id}': held by '{existing.owner_task_id}'")
                return None

        lease = ResourceLease(
            lease_id=f"lease_{resource_type.value}_{int(now)}",
            resource_type=resource_type,
            owner_task_id=owner_task_id,
            priority=priority,
            acquired_at=now,
            expires_at=now + lease_sec
        )
        self._active_leases[resource_type] = lease
        return lease

    def release_resource(self, resource_type: ResourceType, owner_task_id: str) -> bool:
        existing = self._active_leases.get(resource_type)
        if existing and existing.owner_task_id == owner_task_id:
            del self._active_leases[resource_type]
            logger.info(f"ResourceArbitrator released resource '{resource_type.value}' for task '{owner_task_id}'")
            return True
        return False

    def is_available(self, resource_type: ResourceType) -> bool:
        existing = self._active_leases.get(resource_type)
        if not existing:
            return True
        return time.time() >= existing.expires_at
