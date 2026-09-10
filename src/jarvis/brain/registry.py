"""
Model Registry & Discovery Subsystem for JARVIS GGUF Language Models.
"""

from pathlib import Path
import re
import os
from typing import List, Optional, Dict, Any
from jarvis.brain.models import ModelInfo
from jarvis.brain.safety import ModelMemoryChecker


class ModelRegistry:
    """Discovers, inspects, and registers local GGUF model files across configured directories."""

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

    SEARCH_DIRS = [
        "models/language",
        "models/gguf",
        "models",
    ]

    def __init__(self, models_dir: Optional[str | Path] = None, search_dirs: Optional[List[str]] = None):
        if models_dir:
            self.search_dirs = [Path(models_dir)]
        else:
            self.search_dirs = [Path(d) for d in (search_dirs or self.SEARCH_DIRS)]
        self.models_dir = self.search_dirs[0] if self.search_dirs else Path("models/language")


    def discover_models(self) -> List[ModelInfo]:
        """Scans search_dirs for supported GGUF model files."""
        models: List[ModelInfo] = []
        seen_paths = set()

        for sdir in self.search_dirs:
            if not sdir.exists():
                continue
            for file in sdir.glob("*.gguf"):
                resolved_str = str(file.resolve())
                if file.is_file() and resolved_str not in seen_paths:
                    seen_paths.add(resolved_str)
                    size = file.stat().st_size
                    quant = self._extract_quantization(file.name)
                    models.append(
                        ModelInfo(
                            name=file.stem,
                            path=resolved_str,
                            size_bytes=size,
                            size_mb=round(size / (1024 * 1024), 2),
                            format="GGUF",
                            quantization=quant,
                            backend="llama_cpp",
                            available=True,
                            loaded=False
                        )
                    )

        return models

    def get_default_or_first_model(self, configured_path: Optional[str] = None) -> Optional[ModelInfo]:
        """Selects configured model or first available safe model."""
        discovered = self.discover_models()

        if configured_path:
            p = Path(configured_path).resolve()
            for m in discovered:
                if Path(m.path).resolve() == p or m.name == configured_path or m.name == Path(configured_path).name:
                    return m

        for m in discovered:
            is_safe, _ = ModelMemoryChecker.check_memory_safety(m.path)
            if is_safe:
                return m

        if discovered:
            return discovered[0]

        return None

    def validate_model_path(self, path: str) -> Tuple[bool, str]:
        """Validates file existence, extension, and readability."""
        if not os.path.exists(path):
            return False, f"Model file not found at: '{path}'"

        if not path.lower().endswith(".gguf"):
            return False, f"File format for '{path}' is not .gguf"

        if not os.access(path, os.R_OK):
            return False, f"Model file '{path}' is not readable."

        return True, "Valid GGUF model file."

    @staticmethod
    def get_missing_model_message() -> str:
        return (
            "No local language model is configured.\n"
            "Please place a compatible local GGUF model in models/language/ or models/gguf/ "
            "and configure it in config/models.yaml."
        )

    def _extract_quantization(self, filename: str) -> str:
        for pattern, label in self.QUANT_PATTERNS:
            if re.search(pattern, filename, re.IGNORECASE):
                return label
        return "GGUF"
