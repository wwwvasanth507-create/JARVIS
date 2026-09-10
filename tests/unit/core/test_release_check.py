"""
Unit tests for Production Release Check Gate.
"""

from jarvis.core.release import JarvisReleaseCheck, ReleaseStatus


def test_jarvis_release_check_execution():
    result = JarvisReleaseCheck.run_release_check()
    assert "status" in result
    assert "is_ready" in result
    assert result["status"] in (ReleaseStatus.READY.value, ReleaseStatus.BLOCKED.value)
    assert result["check_count"] >= 5
    assert len(result["results"]) >= 5
