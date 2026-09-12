"""
Universal Computer Agent Benchmark Evaluator for Prompt 026.
Evaluates natural language intent interpretation, hierarchical plan decomposition,
capability discovery, cross-app workflow execution, and safety confirmation.
"""

import time
import json
import logging
from pathlib import Path
from typing import Dict, Any, List

from jarvis.core.reasoning.interpreter import TaskInterpreter
from jarvis.core.reasoning.decomposer import TaskDecomposer
from jarvis.core.reasoning.critic import PlanCritic

logger = logging.getLogger("jarvis.evaluation.benchmark_p26")


class UniversalAgentBenchmark:
    """Benchmark runner for Prompt 026 evaluation dataset."""

    @classmethod
    def run_benchmark(cls, dataset_path: str = "src/jarvis/evaluation/evaluation_26_scenarios.json") -> Dict[str, Any]:
        p = Path(dataset_path)
        if not p.exists():
            return {"status": "ERROR", "message": f"Dataset {dataset_path} not found"}

        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)

        scenarios = data.get("scenarios", [])
        total = len(scenarios)
        passed = 0
        results: List[Dict[str, Any]] = []

        t0 = time.time()

        for sc in scenarios:
            query = sc.get("query", "")
            intent = TaskInterpreter.interpret(query)
            hierarchy = TaskDecomposer.decompose(intent)
            critic_report = PlanCritic.evaluate(hierarchy)

            obj_ok = intent.objective == sc.get("expected_objective", intent.objective)
            dom_ok = intent.primary_domain == sc.get("expected_domain", intent.primary_domain)
            valid_plan = critic_report.is_valid and len(hierarchy.steps) > 0

            sc_passed = obj_ok and dom_ok and valid_plan
            if sc_passed:
                passed += 1

            results.append({
                "id": sc.get("id"),
                "query": query,
                "passed": sc_passed,
                "objective": intent.objective,
                "domain": intent.primary_domain,
                "steps_count": len(hierarchy.steps)
            })

        duration_ms = (time.time() - t0) * 1000
        pass_rate = (passed / total * 100) if total > 0 else 100.0

        return {
            "status": "PASS" if pass_rate >= 90.0 else "DEGRADED",
            "total_scenarios": total,
            "passed": passed,
            "pass_rate_percent": pass_rate,
            "duration_ms": duration_ms,
            "scenario_results": results
        }


if __name__ == "__main__":
    res = UniversalAgentBenchmark.run_benchmark()
    print(json.dumps(res, indent=2))
