"""
Data structures and configuration types for MyLLM inference engine.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional


@dataclass
class GenerationConfig:
    """Configuration for autoregressive text generation."""
    prompt: str = ""
    max_new_tokens: int = 50
    temperature: float = 1.0
    top_k: int = 0
    top_p: float = 1.0
    repetition_penalty: float = 1.0
    do_sample: bool = True
    seed: Optional[int] = None
    stop_on_eos: bool = True
    eos_token_id: Optional[int] = None
    pad_token_id: Optional[int] = None
    context_overflow_strategy: str = "error"
    use_cache: bool = True

    def __post_init__(self) -> None:
        if self.max_new_tokens <= 0:
            raise ValueError(f"max_new_tokens must be positive, got {self.max_new_tokens}")
        if self.temperature <= 0.0:
            raise ValueError(f"temperature must be positive, got {self.temperature}")
        if self.top_k < 0:
            raise ValueError(f"top_k cannot be negative, got {self.top_k}")
        if not (0.0 < self.top_p <= 1.0):
            raise ValueError(f"top_p must be in (0.0, 1.0], got {self.top_p}")
        if self.repetition_penalty <= 0.0:
            raise ValueError(f"repetition_penalty must be positive, got {self.repetition_penalty}")
        if self.context_overflow_strategy not in {"error", "truncate_prompt"}:
            raise ValueError(
                f"Unsupported context_overflow_strategy '{self.context_overflow_strategy}'. "
                f"Supported: 'error', 'truncate_prompt'."
            )


@dataclass
class GenerationResult:
    """Structured response container for autoregressive generation."""
    prompt: str
    prompt_token_ids: List[int]
    generated_token_ids: List[int]
    text: str
    prompt_tokens: int
    generated_tokens: int
    total_tokens: int
    generation_time: float
    tokens_per_second: float
    stopped_on_eos: bool
    stopped_reason: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to serializable dictionary."""
        return asdict(self)
