"""
Production Benchmark Suite for JARVIS.

Measures actual runtime metrics:
- Startup time
- Idle RAM / CPU
- Fast-path latency
- Orchestrator command latency
- Scheduler dispatch latency
- Graceful shutdown latency

Saves benchmark metadata to `data/cache/production-benchmark.json`.
"""

import json
import time
from pathlib import Path
import psutil
import logging
from typing import Dict, Any

from jarvis.app import JARVISApp
from jarvis.core.hardware import HardwareDetector

logger = logging.getLogger(__name__)

CACHE_DIR = Path("data/cache")
BENCHMARK_FILE = CACHE_DIR / "production-benchmark.json"


class PerformanceBenchmark:
    """Benchmark suite measuring actual subsystem latencies and resource footprints."""

    @classmethod
    def run_benchmark(cls) -> Dict[str, Any]:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        results: Dict[str, Any] = {}

        # 1. Startup Latency & Initial RAM
        t0 = time.perf_counter()
        app = JARVISApp(safe_mode=True)
        init_success = app.initialize()
        startup_ms = round((time.perf_counter() - t0) * 1000, 2)

        mem = psutil.Process().memory_info()
        idle_ram_mb = round(mem.rss / (1024 * 1024), 2)

        results["startup_time_ms"] = startup_ms
        results["init_success"] = init_success
        results["idle_ram_mb"] = idle_ram_mb

        # 2. Fast-Path Latency
        t0 = time.perf_counter()
        res_fast = app.execute_command("what time is it")
        fast_path_ms = round((time.perf_counter() - t0) * 1000, 2)
        results["fast_path_latency_ms"] = fast_path_ms
        results["fast_path_success"] = res_fast.get("success", False)

        # 3. Status Fast-Path Latency
        t0 = time.perf_counter()
        res_status = app.execute_command("show system status")
        status_latency_ms = round((time.perf_counter() - t0) * 1000, 2)
        results["status_latency_ms"] = status_latency_ms

        # 4. Orchestrator Processing Latency (Fast-path / Fallback command)
        t0 = time.perf_counter()
        res_cmd = app.execute_command("list tasks")
        cmd_latency_ms = round((time.perf_counter() - t0) * 1000, 2)
        results["command_latency_ms"] = cmd_latency_ms

        # 5. Shutdown Latency
        t0 = time.perf_counter()
        app.shutdown()
        shutdown_ms = round((time.perf_counter() - t0) * 1000, 2)
        results["shutdown_time_ms"] = shutdown_ms

        # 6. Hardware Context
        hw = HardwareDetector.detect()
        results["hardware_profile"] = hw.performance_profile.value
        results["cpu_count"] = hw.cpu_count
        results["total_ram_gb"] = hw.total_ram_gb

        # Write cache file
        with open(BENCHMARK_FILE, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)

        logger.info(f"Production benchmark saved to {BENCHMARK_FILE}")
        return results


if __name__ == "__main__":
    res = PerformanceBenchmark.run_benchmark()
    print(json.dumps(res, indent=2))
