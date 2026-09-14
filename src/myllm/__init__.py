"""
MyLLM: A self-contained GPT-style decoder-only Transformer language model built from scratch.

First and primary target is CPU-only execution with zero external pretrained models.
"""

__version__ = "0.1.0"
__author__ = "ML Systems Engineer"

from myllm.config import AppConfig, load_config
from myllm.utils.device import resolve_device, configure_cpu_threads, get_device_info, DeviceNotAllowedError
from myllm.utils.seed import set_seed
from myllm.utils.logging import get_logger

__all__ = [
    "AppConfig",
    "load_config",
    "resolve_device",
    "configure_cpu_threads",
    "get_device_info",
    "DeviceNotAllowedError",
    "set_seed",
    "get_logger",
]
