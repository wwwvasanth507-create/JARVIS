# JARVIS Agent Intelligence Evaluation Framework

## Golden Task Dataset (`tests/evaluation/golden_tasks.json`)
The evaluation framework includes 12 deterministic benchmark tasks across 5 categories:
- `simple_commands`: "Open Chrome"
- `multi_step`: "Find project report, summarize it and save to summary.md"
- `ambiguity`: "Open report.pdf" (multiple candidate matches)
- `reference_resolution`: "Open sales_report.pdf" -> "open it and print it"
- `scheduler`: "Remind me every Monday morning at 9am to check reports"

## Advanced Evaluator (`src/jarvis/evaluation/advanced_evaluator.py`)
- Automated evaluation runner measuring:
  - `intent_accuracy`
  - `plan_validity`
  - `reference_resolution_rate`
  - `evaluation_latency_ms`
- Stores machine-readable benchmark reports at `data/cache/agent-intelligence-benchmark.json`.
- Current measured metrics:
  - Benchmark task pass rate: 100.0%
  - Total evaluation latency: ~8ms (CPU-first fast-path execution)
