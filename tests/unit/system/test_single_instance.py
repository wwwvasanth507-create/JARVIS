"""
Unit tests for Single Instance Lock Manager.
"""

from jarvis.system.single_instance import SingleInstanceLock


def test_single_instance_acquire_and_release():
    lock = SingleInstanceLock(mutex_name="TEST_JARVIS_SINGLE_INSTANCE_MUTEX_UNIQUE")
    assert lock.acquire() is True
    
    # Attempting to acquire a second lock with same name should fail
    lock2 = SingleInstanceLock(mutex_name="TEST_JARVIS_SINGLE_INSTANCE_MUTEX_UNIQUE")
    assert lock2.acquire() is False

    lock.release()

    # After release, acquire should succeed again
    lock3 = SingleInstanceLock(mutex_name="TEST_JARVIS_SINGLE_INSTANCE_MUTEX_UNIQUE")
    assert lock3.acquire() is True
    lock3.release()
