"""
Performance Benchmarking Suite for JARVIS CPU-First Architecture.
"""

import time
import pytest
from jarvis.system.hardware import HardwareDetector
from jarvis.brain.fast_path import FastIntentRouter
from jarvis.system.task_queue import TaskQueue, TaskPriority


def test_benchmark_hardware_detection_latency():
    start = time.perf_counter()
    profile = HardwareDetector.detect()
    elapsed_ms = (time.perf_counter() - start) * 1000.0

    print(f"\n[BENCHMARK] Hardware Detection Latency: {elapsed_ms:.2f} ms")
    assert profile.cpu_name != ""
    # Target latency < 500 ms (allowing fallback WMIC execution on Windows)
    assert elapsed_ms < 500.0


def test_benchmark_fast_intent_matching_latency():
    test_queries = [
        "Open Chrome",
        "Close Notepad",
        "Take a screenshot",
        "Pause music",
        "Turn volume down",
        "Complex request requiring LLM reasoning",
    ]

    start = time.perf_counter()
    iterations = 1000
    for _ in range(iterations):
        for q in test_queries:
            FastIntentRouter.match(q)
    elapsed_ms = (time.perf_counter() - start) * 1000.0
    avg_per_match_ms = elapsed_ms / (iterations * len(test_queries))

    print(f"\n[BENCHMARK] Fast Intent Matching: {avg_per_match_ms:.4f} ms per match")
    # Sub-millisecond target for fast regex matching
    assert avg_per_match_ms < 1.0


def test_benchmark_task_queue_throughput():
    queue = TaskQueue()
    count = 5000

    start = time.perf_counter()
    for i in range(count):
        queue.enqueue(f"task_{i}", priority=TaskPriority.NORMAL)
    for _ in range(count):
        t = queue.pop_next()
        if t:
            queue.mark_completed(t.id)
    elapsed_ms = (time.perf_counter() - start) * 1000.0

    print(f"\n[BENCHMARK] Task Queue Throughput: {count} tasks processed in {elapsed_ms:.2f} ms")
    assert elapsed_ms < 1000.0
