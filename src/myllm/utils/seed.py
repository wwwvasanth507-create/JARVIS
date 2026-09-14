"""
Reproducibility and Random Seed Utility for MyLLM.

Ensures deterministic execution across Python, NumPy, and PyTorch on CPU.
"""

import os
import random
import logging
from typing import Optional
import numpy as np
import torch

logger = logging.getLogger(__name__)


def set_seed(seed: int = 42, deterministic_cpu: bool = True) -> int:
    """
    Set random seeds for Python, NumPy, and PyTorch to maximize reproducibility on CPU.

    Args:
        seed: The integer seed value. Defaults to 42.
        deterministic_cpu: If True, configures PyTorch deterministic algorithms where supported.

    Returns:
        The seed integer that was set.
    """
    # Python built-in random
    random.seed(seed)

    # Python hash seed
    os.environ["PYTHONHASHSEED"] = str(seed)

    # NumPy random
    np.random.seed(seed)

    # PyTorch CPU manual seed
    torch.manual_seed(seed)

    if deterministic_cpu:
        try:
            torch.use_deterministic_algorithms(True, warn_only=True)
        except Exception as exc:
            logger.debug(f"Deterministic algorithms warning flag set exception: {exc}")

    logger.debug(f"Random seed set to {seed} (CPU deterministic={deterministic_cpu})")
    return seed
