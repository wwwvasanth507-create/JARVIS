#!/usr/bin/env python3
"""
Diagnostic script for MyLLM environment.

Prints:
- Python version
- PyTorch version
- Selected device
- CPU thread configuration
- Whether CUDA is available
- Whether the project is actually using CUDA

The project explicitly selects CPU regardless of CUDA availability.
"""

import sys
import platform
from pathlib import Path

# Ensure src is in python path
repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root / "src"))

import torch
from myllm.config import load_config
from myllm.utils.device import resolve_device, configure_cpu_threads, get_device_info


def main() -> int:
    print("=" * 60)
    print("           MyLLM System Environment Diagnostics           ")
    print("=" * 60)

    # 1. Python Details
    py_version = platform.python_version()
    py_compiler = platform.python_compiler()
    py_platform = platform.platform()
    print(f"Python Version           : {py_version} ({py_compiler})")
    print(f"Platform / OS            : {py_platform}")

    # 2. PyTorch Details
    torch_version = torch.__version__
    print(f"PyTorch Version          : {torch_version}")

    # 3. Load Project Config
    config = load_config()
    print(f"Configured Device        : {config.system.device}")
    print(f"Strict CPU Enforced      : {config.system.strict_cpu}")

    # 4. Resolve Device & Threads
    device = resolve_device(
        requested_device=config.system.device,
        strict_cpu=config.system.strict_cpu,
    )
    if config.system.num_threads:
        configure_cpu_threads(config.system.num_threads)

    info = get_device_info(strict_cpu=config.system.strict_cpu)

    print(f"Selected Device          : {device} (type: {device.type})")
    print(f"CPU Intra-op Threads     : {info['num_cpu_threads']}")
    print(f"CPU Inter-op Threads     : {info['num_interop_threads']}")

    # 5. CUDA / GPU Status
    cuda_available = info["cuda_available_on_system"]
    is_using_cuda = info["is_using_cuda"]
    print(f"CUDA Available on System : {cuda_available}")
    print(f"Project Using CUDA       : {is_using_cuda}")

    # 6. Tensor Operation Smoke Test on CPU
    x = torch.ones((2, 2), device=device)
    y = x + x
    print(f"CPU Tensor Test Result   : Shape {list(y.shape)}, Device={y.device}, Sum={float(y.sum())}")

    print("=" * 60)
    if is_using_cuda:
        print("ERROR: Project is using CUDA! CPU-only policy violated.")
        return 1
    elif device.type != "cpu":
        print(f"ERROR: Selected device is {device}, not CPU!")
        return 1
    else:
        print("SUCCESS: Environment is verified. Pure CPU execution confirmed.")
        print("=" * 60)
        return 0


if __name__ == "__main__":
    sys.exit(main())
