"""
Evaluation Subsystem for MyLLM.

Provides:
- Token-weighted validation loss and perplexity (evaluate_perplexity).
- Metrics container and calculation (EvaluationMetrics, calculate_perplexity).
- Generation evaluation across prompt sets (GenerationEvaluator, GenerationEvalRecord).
- Reporting and serialization (format_perplexity_report, save_metrics_json).
"""

from myllm.evaluation.evaluator import GenerationEvalRecord, GenerationEvaluator
from myllm.evaluation.metrics import EvaluationMetrics, calculate_perplexity
from myllm.evaluation.perplexity import evaluate_perplexity
from myllm.evaluation.report import format_perplexity_report, save_metrics_json

__all__ = [
    "EvaluationMetrics",
    "calculate_perplexity",
    "evaluate_perplexity",
    "GenerationEvaluator",
    "GenerationEvalRecord",
    "format_perplexity_report",
    "save_metrics_json",
]
