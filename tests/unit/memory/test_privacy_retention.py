"""
Unit tests for MemoryPrivacyPolicy and RetentionManager.
"""

import time
import pytest
from jarvis.memory.database import DatabaseManager
from jarvis.memory.errors import PrivacyViolationError
from jarvis.memory.migrations import SchemaMigrator
from jarvis.memory.models import MemoryItem, PrivacyLevel
from jarvis.memory.privacy import MemoryPrivacyPolicy
from jarvis.memory.retention import RetentionManager
from jarvis.memory.storage import MemoryStorage


def test_privacy_policy_blocks_passwords_and_tokens():
    policy = MemoryPrivacyPolicy()

    # Passwords
    item_pwd = MemoryItem(key="secret", content="password=SuperSecret123!")
    with pytest.raises(PrivacyViolationError) as exc_pwd:
        policy.validate(item_pwd)
    assert "password" in str(exc_pwd.value)

    # API Keys
    item_key = MemoryItem(key="api_key", content="api_key = sk_live_12345")
    with pytest.raises(PrivacyViolationError) as exc_key:
        policy.validate(item_key)
    assert "api_key" in str(exc_key.value)

    # Sensitive Privacy Level
    item_sens = MemoryItem(key="private_data", content="harmless text", privacy_level=PrivacyLevel.SENSITIVE)
    with pytest.raises(PrivacyViolationError):
        policy.validate(item_sens)


def test_retention_expiration_and_forget():
    db_mgr = DatabaseManager(db_path=":memory:")
    SchemaMigrator(db_mgr).migrate()
    storage = MemoryStorage(db_mgr)
    retention = RetentionManager(storage)

    # Normal memory
    storage.save_memory(MemoryItem(key="normal_key", content="val1"))

    # Expired memory
    past_time = time.time() - 10.0
    storage.save_memory(MemoryItem(key="expired_key", content="val2", expires_at=past_time))

    cleaned = retention.cleanup_expired_memories()
    assert cleaned == 1
    assert storage.get_memory_by_key("expired_key") is None
    assert storage.get_memory_by_key("normal_key") is not None

    # Forget key
    forgotten = retention.forget_key("normal_key")
    assert forgotten is True
    assert storage.get_memory_by_key("normal_key") is None
