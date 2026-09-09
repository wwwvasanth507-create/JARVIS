"""
Model Registry & Discovery Subsystem for JARVIS GGUF Language Models.
"""

from pathlib import Path
import re
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ModelInfo(BaseModel):
    name: str
    path: str
    size_bytes: int
    size_mb: float
    format: str = "GGUF"
    quantization: str = "Unknown"


class ModelRegistry:
    """Discovers and inspects local GGUF model files in models/language/."""

    QUANT_PATTERNS = [
        (r"Q4_K_M", "Q4_K_M"),
        (r"Q4_K_S", "Q4_K_S"),
        (r"Q4_0", "Q4_0"),
        (r"Q5_K_M", "Q5_K_M"),
        (r"Q5_K_S", "Q5_K_S"),
        (r"Q5_0", "Q5_0"),
        (r"Q6_K", "Q6_K"),
        (r"Q8_0", "Q8_0"),
        (r"Q3_K_M", "Q3_K_M"),
        (r"Q2_K", "Q2_K"),
    ]

    def __init__(self, models_dir: str | Path = "models/language"):
        self.models_dir = Path(models_dir)

    def discover_models(self) -> List[ModelInfo]:
        """Scans models_dir for supported GGUF model files."""
        if not self.models_dir.exists():
            return []

        models: List[ModelInfo] = []
        for file in self.models_dir.glob("*.gguf"):
            if file.is_file():
                size = file.stat().st_size
                quant = self._extract_quantization(file.name)
                models.append(
                    ModelInfo(
                        name=file.stem,
                        path=str(file.resolve()),
                        size_bytes=size,
                        size_mb=round(size / (1024 * 1024), 2),
                        format="GGUF",
                        quantization=quant,
                    )
                )
        return models

    def get_default_or_first_model(self, configured_path: Optional[str] = None) -> Optional[ModelInfo]:
        discovered = self.discover_models()
        if configured_path:
            p = Path(configured_path).resolve()
            for m in discovered:
                if Path(m.path).resolve() == p or m.name == configured_path:
                    return m

        if discovered:
            return discovered[0]

        return None

    @staticmethod
    def get_missing_model_message() -> str:
        return (
            "No local language model is configured.\n"
            "Please place a compatible local GGUF model in the models/language/ directory "
            "and configure it in config/models.yaml."
        )

    def _extract_quantization(self, filename: str) -> str:
        for pattern, label in self.QUANT_PATTERNS:
            if re.search(pattern, filename, re.IGNORECASE):
                return label
        return "GGUF"
