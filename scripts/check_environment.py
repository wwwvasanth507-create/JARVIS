#!/usr/bin/env python3
"""
Comprehensive System Environment & Diagnostic Utility for MyLLM.

Reports:
1. Python version and compiler details
2. Operating system and platform architecture
3. CPU hardware specifications (processor model, physical cores, logical threads)
4. PyTorch version and CPU thread settings
5. CUDA availability vs active device enforcement (Strict CPU-Only Mode)
6. Python package installation status (`myllm` package discovery and version)
7. Frontend environment status (Node.js, npm, node_modules status)
8. Tensor smoke test on CPU device

Enforces:
- Pure CPU execution policy (exits with code 1 if CUDA is actively used or requested)
"""

from __future__ import annotations

import importlib.metadata
import importlib.util
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import psutil

# Ensure src is on sys.path if not installed in current environment
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

import torch

try:
    import myllm
    MYLLM_INSTALLED = True
    MYLLM_VERSION = getattr(myllm, "__version__", "unknown")
except ImportError:
    MYLLM_INSTALLED = False
    MYLLM_VERSION = "not installed"

from myllm.config import load_config
from myllm.utils.device import configure_cpu_threads, get_device_info, resolve_device


def detect_cpu_model() -> str:
    """Detect CPU processor name or fallback gracefully."""
    proc = platform.processor()
    if proc:
        return proc
    return platform.machine() or "Unknown CPU"


def detect_frontend_environment() -> dict[str, str]:
    """Inspect Node.js, npm, and frontend dependencies if present."""
    status = {
        "node_installed": "Not detected",
        "npm_installed": "Not detected",
        "frontend_modules": "Missing (run 'cd frontend && npm install')",
    }

    node_bin = shutil.which("node")
    if node_bin:
        try:
            res = subprocess.run([node_bin, "--version"], capture_output=True, text=True, check=False)
            if res.returncode == 0:
                status["node_installed"] = res.stdout.strip()
        except Exception:
            pass

    npm_bin = shutil.which("npm")
    if npm_bin:
        try:
            # On Windows npm is often npm.cmd
            res = subprocess.run([npm_bin, "--version"], capture_output=True, text=True, shell=True, check=False)
            if res.returncode == 0:
                status["npm_installed"] = res.stdout.strip()
        except Exception:
            pass

    fe_node_modules = REPO_ROOT / "frontend" / "node_modules"
    if fe_node_modules.is_dir():
        status["frontend_modules"] = f"Installed ({fe_node_modules})"

    return status


def detect_package_status() -> dict[str, str]:
    """Inspect whether myllm is installed in site-packages/editable mode."""
    info = {
        "package_installed": "No (running from source path)",
        "version": MYLLM_VERSION,
        "location": "unknown",
    }
    spec = importlib.util.find_spec("myllm")
    if spec and spec.origin:
        info["location"] = spec.origin
        try:
            dist_version = importlib.metadata.version("myllm")
            info["package_installed"] = f"Yes (v{dist_version})"
        except importlib.metadata.PackageNotFoundError:
            info["package_installed"] = "Loaded from local source path"
    return info


def main() -> int:
    print("=" * 70)
    print("           MyLLM System Environment Diagnostics           ")
    print("                 >>> CPU-ONLY MODE <<<                    ")
    print("=" * 70)

    # 1. Python Details
    py_version = platform.python_version()
    py_compiler = platform.python_compiler()
    py_platform = platform.platform()
    print("[1/6] Python & Operating System:")
    print(f"  Python Version         : {py_version} ({py_compiler})")
    print(f"  OS / Platform          : {py_platform}")
    print(f"  Executable Path        : {sys.executable}")

    # 2. CPU Hardware
    processor = detect_cpu_model()
    arch = platform.machine()
    phys_cores = psutil.cpu_count(logical=False) or 1
    log_cores = psutil.cpu_count(logical=True) or 1
    total_ram_gb = round(psutil.virtual_memory().total / (1024 ** 3), 2)
    print("\n[2/6] CPU Hardware Specifications:")
    print(f"  Processor Name         : {processor}")
    print(f"  Architecture           : {arch}")
    print(f"  Physical Cores         : {phys_cores}")
    print(f"  Logical Threads        : {log_cores}")
    print(f"  Total System RAM       : {total_ram_gb} GB")

    # 3. PyTorch & Compute Device
    torch_version = torch.__version__
    config = load_config()
    device = resolve_device(
        requested_device=config.system.device,
        strict_cpu=config.system.strict_cpu,
    )
    if config.system.num_threads:
        configure_cpu_threads(config.system.num_threads)
    dev_info = get_device_info(strict_cpu=config.system.strict_cpu)

    print("\n[3/6] PyTorch & Device Policy:")
    print(f"  PyTorch Version        : {torch_version}")
    print(f"  Strict CPU Policy      : {config.system.strict_cpu} (Enforced)")
    print(f"  Selected Device        : {device} (type: {device.type.upper()})")
    print(f"  Intra-op Threads       : {dev_info['num_cpu_threads']}")
    print(f"  Inter-op Threads       : {dev_info['num_interop_threads']}")
    print(f"  CUDA Detected on Host  : {dev_info['cuda_available_on_system']}")
    print(f"  Project Using CUDA     : {dev_info['is_using_cuda']} (MUST BE False)")

    # 4. Package Installation
    pkg_status = detect_package_status()
    print("\n[4/6] Python Package Installation:")
    print(f"  myllm Installed        : {pkg_status['package_installed']}")
    print(f"  myllm Version          : {pkg_status['version']}")
    print(f"  Module Origin          : {pkg_status['location']}")

    # 5. Frontend Environment
    fe_status = detect_frontend_environment()
    print("\n[5/6] Frontend Toolchain:")
    print(f"  Node.js Version        : {fe_status['node_installed']}")
    print(f"  npm Version            : {fe_status['npm_installed']}")
    print(f"  Dependencies Status    : {fe_status['frontend_modules']}")

    # 6. Tensor Smoke Test on CPU
    x = torch.ones((2, 2), device=device)
    y = x + x
    print("\n[6/6] CPU Tensor Smoke Test:")
    print(f"  Result Shape           : {list(y.shape)}")
    print(f"  Result Device          : {y.device}")
    print(f"  Sum Value              : {float(y.sum())}")

    print("=" * 70)
    if dev_info["is_using_cuda"]:
        print("CRITICAL FAILURE: CUDA is actively used! Strict CPU policy violated.")
        return 1
    elif device.type != "cpu":
        print(f"CRITICAL FAILURE: Selected device is {device}, not CPU!")
        return 1
    else:
        print("DIAGNOSTIC STATUS: PASS")
        print("System verified for reproducible CPU-only local execution.")
        print("=" * 70)
        return 0


if __name__ == "__main__":
    sys.exit(main())
