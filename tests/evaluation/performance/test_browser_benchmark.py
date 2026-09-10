"""
Browser Automation Performance Benchmark Test for JARVIS.
Measures actual startup time, navigation time, page extraction time, and tab latencies on CPU.
"""

from pathlib import Path
import time
import pytest
from jarvis.browser.manager import BrowserManager
from jarvis.core.config import BrowserSettings


def test_browser_performance_benchmarks():
    """Measures actual execution latencies for browser automation operations."""
    fixture_path = Path("tests/browser/fixtures/sample_page.html").resolve()
    assert fixture_path.exists()
    file_url = fixture_path.as_uri()

    settings = BrowserSettings(
        headless=True,
        reuse_session=True,
        allowed_schemes=["http", "https", "file"],
    )
    manager = BrowserManager(settings=settings)

    # 1. Startup latency
    t0 = time.perf_counter()
    manager.start()
    startup_time_ms = (time.perf_counter() - t0) * 1000.0
    assert manager.is_running() is True
    assert startup_time_ms > 0

    try:
        # 2. Navigation latency
        t0 = time.perf_counter()
        res = manager.open(file_url)
        nav_time_ms = (time.perf_counter() - t0) * 1000.0
        assert res.success is True
        assert nav_time_ms > 0

        # 3. Extraction latency
        t0 = time.perf_counter()
        read_res = manager.read_page()
        extract_time_ms = (time.perf_counter() - t0) * 1000.0
        assert read_res["title"] == "JARVIS Test Page"
        assert extract_time_ms > 0

        # 4. Tab creation & switch latency
        t0 = time.perf_counter()
        tab_res = manager.new_tab()
        tab_time_ms = (time.perf_counter() - t0) * 1000.0
        assert tab_res.success is True

        # 5. Screenshot latency
        t0 = time.perf_counter()
        shot_path = manager.screenshot()
        shot_time_ms = (time.perf_counter() - t0) * 1000.0
        assert Path(shot_path).exists()

        # Log measured benchmark numbers for transparency
        print(f"\n[BENCHMARK] Browser Startup: {startup_time_ms:.2f} ms")
        print(f"[BENCHMARK] Navigation Latency: {nav_time_ms:.2f} ms")
        print(f"[BENCHMARK] Extraction Latency: {extract_time_ms:.2f} ms")
        print(f"[BENCHMARK] Tab Creation Latency: {tab_time_ms:.2f} ms")
        print(f"[BENCHMARK] Screenshot Latency: {shot_time_ms:.2f} ms")

    finally:
        manager.stop()
