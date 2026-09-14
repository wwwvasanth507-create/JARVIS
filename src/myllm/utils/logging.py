"""
Logging Utility for MyLLM.

Provides structured and clean logging to console and optional rotating/persisted files.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Optional, Union


def get_logger(
    name: str = "myllm",
    log_file: Optional[Union[str, Path]] = None,
    level: Union[int, str] = logging.INFO,
) -> logging.Logger:
    """
    Configure and return a standardized logger for MyLLM.

    Args:
        name: Logger hierarchy name. Defaults to 'myllm'.
        log_file: Optional file path to write log output.
        level: Logging level (e.g. logging.INFO, "DEBUG").

    Returns:
        Configured logging.Logger instance.
    """
    logger = logging.getLogger(name)

    if isinstance(level, str):
        level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(level)

    # Avoid duplicate handlers if get_logger is called repeatedly
    if not logger.handlers:
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Standard console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # Optional file handler
        if log_file:
            path = Path(log_file)
            path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(path, encoding="utf-8")
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

    return logger
