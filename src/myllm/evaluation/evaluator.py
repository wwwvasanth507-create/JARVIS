"""
Generation Evaluation Tool for MyLLM.

Evaluates generation behavior, latency, throughput, and stopping conditions
across a test set of prompts. Does not claim semantic quality.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional
from myllm.inference.generator import Generator
from myllm.inference.types import GenerationConfig


@dataclass
class GenerationEvalRecord:
    """Record of generation performance and output for a single prompt."""
    prompt: str
    generated_text: str
    token_count: int
    generation_time_sec: float
    tokens_per_sec: float
    stopping_reason: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class GenerationEvaluator:
    """
    Evaluator for autoregressive generation runs across multiple benchmark prompts.
    """

    DEFAULT_PROMPTS = [
        "The quick brown fox",
        "Deep learning models require",
        "Once upon a time in a faraway land",
        "The fundamental law of physics states that",
    ]

    def __init__(self, generator: Generator) -> None:
        self.generator = generator

    def evaluate_prompts(
        self,
        prompts: Optional[List[str]] = None,
        config: Optional[GenerationConfig] = None,
    ) -> List[GenerationEvalRecord]:
        """
        Run generation on a list of prompts and record performance metrics.

        Args:
            prompts: List of prompt strings (defaults to DEFAULT_PROMPTS if None).
            config: GenerationConfig to apply to all prompts.

        Returns:
            List of GenerationEvalRecord.
        """
        if prompts is None:
            prompts = self.DEFAULT_PROMPTS

        records: List[GenerationEvalRecord] = []
        for p in prompts:
            res = self.generator.generate(prompt=p, config=config)
            records.append(
                GenerationEvalRecord(
                    prompt=res.prompt,
                    generated_text=res.text,
                    token_count=res.generated_tokens,
                    generation_time_sec=res.generation_time,
                    tokens_per_sec=res.tokens_per_second,
                    stopping_reason=res.stopped_reason,
                )
            )
        return records

    @staticmethod
    def generate_summary_table(records: List[GenerationEvalRecord]) -> str:
        """Format evaluation records as a clean markdown table."""
        lines = [
            "| Prompt | Tokens | Time (s) | Tokens/s | Stop Reason | Completion Preview |",
            "| :--- | :---: | :---: | :---: | :---: | :--- |",
        ]
        for r in records:
            preview = (r.generated_text[:40] + "...") if len(r.generated_text) > 40 else r.generated_text
            preview_clean = preview.replace("\n", " ").replace("|", "\\|")
            prompt_clean = (r.prompt[:25] + "...") if len(r.prompt) > 25 else r.prompt
            prompt_clean = prompt_clean.replace("\n", " ").replace("|", "\\|")
            lines.append(
                f"| {prompt_clean} | {r.token_count} | {r.generation_time_sec:.3f} | "
                f"{r.tokens_per_sec:.1f} | {r.stopping_reason} | {preview_clean} |"
            )
        return "\n".join(lines)
