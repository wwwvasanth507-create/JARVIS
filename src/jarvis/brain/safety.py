"""
RAM Safety and Memory Check Utility for Local Models.
"""

import os
import psutil
from pathlib import Path
from typing import Tuple
from jarvis.brain.errors import ModelMemoryUnavailableError


class ModelMemoryChecker:
    """
    Validates model memory requirements against system RAM before loading GGUF model files.
    """

    @staticmethod
    def estimate_model_ram_bytes(model_path: str, headroom_factor: float = 1.2) -> int:
        if not os.path.exists(model_path):
            return 0
        file_size = os.path.getsize(model_path)
        return int(file_size * headroom_factor)

    @classmethod
    def check_memory_safety(
        cls,
        model_path: str,
        min_free_ram_gb: float = 1.5,
        headroom_factor: float = 1.2
    ) -> Tuple[bool, str]:
        """
        Checks if available RAM can safely accommodate the model file.
        Returns (is_safe, message).
        """
        if not os.path.exists(model_path):
            return False, f"Model file not found: {model_path}"

        estimated_needed = cls.estimate_model_ram_bytes(model_path, headroom_factor)
        needed_gb = estimated_needed / (1024 ** 3)

        mem = psutil.virtual_memory()
        available_gb = mem.available / (1024 ** 3)

        if available_gb < min_free_ram_gb:
            return False, (
                f"Available system RAM ({available_gb:.2f} GB) is below minimum "
                f"required free RAM threshold of {min_free_ram_gb} GB."
            )

        if needed_gb > available_gb:
            return False, (
                f"Estimated model memory requirement ({needed_gb:.2f} GB) "
                f"exceeds available system RAM ({available_gb:.2f} GB)."
            )

        return True, "Memory safety check passed."

    @classmethod
    def validate_or_raise(cls, model_path: str, min_free_ram_gb: float = 1.5, headroom_factor: float = 1.2) -> None:
        is_safe, msg = cls.check_memory_safety(model_path, min_free_ram_gb, headroom_factor)
        if not is_safe:
            raise ModelMemoryUnavailableError(f"MODEL_MEMORY_UNAVAILABLE: {msg}")
