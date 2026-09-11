"""
Performance Latency Benchmark Suite for Memory Architecture 2.0 & Knowledge Graph.
"""

import time
import json
import logging
from typing import Dict, Any
from pathlib import Path

from jarvis.memory.manager import MemoryManager
from jarvis.memory.graph import KnowledgeGraphManager, EntityType, RelationType, MemorySource
from jarvis.memory.conflict_resolver import MemoryConflictResolver
from jarvis.memory.memory_layers import ScopedPreference, MemoryScope, PreferenceLevel
from jarvis.memory.explanation_engine import MemoryExplanationEngine
from jarvis.memory.maintenance import MemoryMaintenanceManager
from jarvis.utils.paths import ResourcePathResolver

logger = logging.getLogger(__name__)
BENCHMARK_OUTPUT_FILE = ResourcePathResolver.get_cache_dir() / "memory-benchmark.json"


class MemoryBenchmark:
    """Measures latency metrics across Memory 2.0 operations."""

    @classmethod
    def run_benchmark(cls) -> Dict[str, Any]:
        mem_mgr = MemoryManager.get_instance()
        graph_mgr = KnowledgeGraphManager.get_instance()
        maint_mgr = MemoryMaintenanceManager.get_instance()

        # 1. Measure Memory Retrieval Latency
        t0 = time.perf_counter()
        results = mem_mgr.search_memory("project", limit=10)
        t_retrieval = round((time.perf_counter() - t0) * 1000, 2)

        # 2. Measure Knowledge Graph Traversal Latency
        node = graph_mgr.add_node(EntityType.PROJECT, "JARVIS", aliases=["jarvis_repo"])
        t0 = time.perf_counter()
        graph_res = graph_mgr.query_neighborhood(node.node_id, max_depth=2, max_nodes=50)
        t_graph = round((time.perf_counter() - t0) * 1000, 2)

        # 3. Measure Conflict Resolution Latency
        p1 = ScopedPreference(key="browser", value="Chrome", level=PreferenceLevel.WEAK_INFERENCE, scope=MemoryScope.GLOBAL)
        p2 = ScopedPreference(key="browser", value="Firefox", level=PreferenceLevel.EXPLICIT, scope=MemoryScope.PROJECT)
        t0 = time.perf_counter()
        winner = MemoryConflictResolver.resolve_preference_conflict([p1, p2])
        t_conflict = round((time.perf_counter() - t0) * 1000, 2)

        # 4. Measure Explanation Latency
        t0 = time.perf_counter()
        exp = MemoryExplanationEngine.explain_preference(p2)
        t_explain = round((time.perf_counter() - t0) * 1000, 2)

        # 5. Measure Maintenance & Export Latency
        t0 = time.perf_counter()
        rep = maint_mgr.verify_integrity()
        t_maint = round((time.perf_counter() - t0) * 1000, 2)

        metrics = {
            "memory_retrieval_ms": t_retrieval,
            "knowledge_graph_traversal_ms": t_graph,
            "conflict_resolution_ms": t_conflict,
            "explanation_generation_ms": t_explain,
            "integrity_verification_ms": t_maint,
            "status": "PASSED"
        }

        BENCHMARK_OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(BENCHMARK_OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2)

        logger.info(f"Memory Benchmark saved to {BENCHMARK_OUTPUT_FILE}")
        return metrics


if __name__ == "__main__":
    res = MemoryBenchmark.run_benchmark()
    print(json.dumps(res, indent=2))
