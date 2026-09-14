"""
CPU Device Utility for MyLLM.

Explicitly selects CPU and rejects or safely warns on CUDA/GPU/ROCm requests.
CPU execution is the first-class target.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional
import torch

logger = logging.getLogger(__name__)


class DeviceNotAllowedError(RuntimeError):
    """Raised when a non-CPU device is requested in strict CPU execution mode."""
    pass


def resolve_device(
    requested_device: Optional[str | torch.device] = "cpu",
    strict_cpu: bool = True,
    allow_fallback: bool = False,
) -> torch.device:
    """
    Resolve and validate the compute device, strictly defaulting to and enforcing CPU.

    Args:
        requested_device: Device name ('cpu', 'cuda', etc.) or torch.device instance.
                          Defaults to 'cpu'.
        strict_cpu: If True, non-CPU devices are disallowed.
        allow_fallback: If True and strict_cpu is True, non-CPU requests log a warning
                        and safely fall back to CPU instead of raising DeviceNotAllowedError.

    Returns:
        torch.device initialized to 'cpu'.

    Raises:
        DeviceNotAllowedError: If a non-CPU device is requested and allow_fallback is False.
    """
    if requested_device is None:
        device_str = "cpu"
    elif isinstance(requested_device, torch.device):
        device_str = requested_device.type
    else:
        device_str = str(requested_device).strip().lower()

    # Normalize device string (e.g., 'cuda:0' -> 'cuda')
    base_device = device_str.split(":")[0]

    if base_device != "cpu":
        msg = (
            f"Device '{requested_device}' was requested, but MyLLM is configured for "
            f"strict CPU-only execution. CUDA/GPU/ROCm is not permitted."
        )
        if strict_cpu:
            if allow_fallback:
                logger.warning(f"{msg} Safely falling back to CPU.")
                return torch.device("cpu")
            raise DeviceNotAllowedError(msg)
        else:
            logger.warning(f"Non-CPU device '{requested_device}' allowed by strict_cpu=False override.")
            return torch.device(requested_device)

    return torch.device("cpu")


def configure_cpu_threads(num_threads: Optional[int] = None) -> int:
    """
    Configure the number of CPU threads PyTorch uses for intra-op parallelism.

    Args:
        num_threads: Number of threads to use. If None or <= 0, the current
                     PyTorch thread count is preserved.

    Returns:
        The active number of PyTorch CPU threads.
    """
    if num_threads is not None and num_threads > 0:
        torch.set_num_threads(num_threads)
        logger.debug(f"PyTorch CPU threads set to {num_threads}")

    return torch.get_num_threads()


def get_device_info(strict_cpu: bool = True) -> Dict[str, Any]:
    """
    Return comprehensive diagnostics regarding compute devices and CPU configuration.

    Args:
        strict_cpu: Current strict CPU enforcement setting.

    Returns:
        Dictionary containing hardware, device, and thread details.
    """
    cuda_available = torch.cuda.is_available()
    cuda_device_count = torch.cuda.device_count() if cuda_available else 0

    return {
        "selected_device": "cpu",
        "device_type": "cpu",
        "strict_cpu_enforced": strict_cpu,
        "num_cpu_threads": torch.get_num_threads(),
        "num_interop_threads": torch.get_num_interop_threads(),
        "cuda_available_on_system": cuda_available,
        "cuda_device_count": cuda_device_count,
        "is_using_cuda": False,  # Always False for MyLLM CPU execution
        "pytorch_version": torch.__version__,
    }
