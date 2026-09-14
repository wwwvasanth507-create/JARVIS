"""
Report generation utilities for MyLLM evaluation.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional, Union
from myllm.evaluation.metrics import EvaluationMetrics


def format_perplexity_report(
    metrics: EvaluationMetrics,
    model_name: str = "MyLLM",
    checkpoint_path: Optional[str] = None,
    dataset_path: Optional[str] = None,
) -> str:
    """Format EvaluationMetrics as an inspectable text report."""
    lines = [
        "=" * 50,
        f"EVALUATION REPORT: {model_name}",
        "=" * 50,
    ]
    if checkpoint_path:
        lines.append(f"Checkpoint:      {checkpoint_path}")
    if dataset_path:
        lines.append(f"Dataset:         {dataset_path}")
    lines.extend([
        f"Batches:         {metrics.num_batches:,}",
        f"Tokens:          {metrics.total_tokens:,}",
        f"Mean Loss:       {metrics.mean_loss:.4f}",
        f"Perplexity:      {metrics.perplexity:.4f}",
        f"Elapsed Time:    {metrics.elapsed_time_sec:.3f} s",
        f"Throughput:      {metrics.tokens_per_sec:.1f} tokens/s (CPU)",
        "=" * 50,
    ])
    return "\n".join(lines)


def save_metrics_json(metrics: EvaluationMetrics, output_path: Union[str, Path], extra: Optional[Dict[str, Any]] = None) -> Path:
    """Save metrics to a JSON file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = metrics.to_dict()
    if extra:
        data.update(extra)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return path
