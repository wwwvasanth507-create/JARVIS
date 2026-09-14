"""
Tests for CPU device utility and CPU-first enforcement.
"""

import pytest
import torch
from myllm.utils.device import (
    DeviceNotAllowedError,
    configure_cpu_threads,
    get_device_info,
    resolve_device,
)


class TestDeviceUtility:
    def test_default_device_is_cpu(self) -> None:
        """Verify that default device resolution always returns CPU."""
        device = resolve_device()
        assert isinstance(device, torch.device)
        assert device.type == "cpu"

    def test_explicit_cpu_resolution(self) -> None:
        """Verify resolving 'cpu' explicitly returns a CPU torch.device."""
        device = resolve_device("cpu")
        assert device == torch.device("cpu")
        assert device.type == "cpu"

    def test_none_returns_cpu(self) -> None:
        """Verify None requested device safely defaults to CPU."""
        device = resolve_device(None)
        assert device.type == "cpu"

    def test_cuda_rejected_under_strict_mode(self) -> None:
        """Verify that requesting CUDA raises DeviceNotAllowedError in strict mode."""
        with pytest.raises(DeviceNotAllowedError) as exc_info:
            resolve_device("cuda")
        assert "not permitted" in str(exc_info.value)

    def test_cuda_index_rejected_under_strict_mode(self) -> None:
        """Verify that requesting cuda:0 raises DeviceNotAllowedError."""
        with pytest.raises(DeviceNotAllowedError):
            resolve_device("cuda:0")

    def test_gpu_alias_rejected_under_strict_mode(self) -> None:
        """Verify that requesting 'gpu' or 'rocm' raises DeviceNotAllowedError."""
        with pytest.raises(DeviceNotAllowedError):
            resolve_device("gpu")
        with pytest.raises(DeviceNotAllowedError):
            resolve_device("rocm")

    def test_fallback_to_cpu_when_allowed(self) -> None:
        """Verify that if allow_fallback=True, non-CPU request safely falls back to CPU."""
        device = resolve_device("cuda", strict_cpu=True, allow_fallback=True)
        assert device.type == "cpu"

    def test_configure_cpu_threads(self) -> None:
        """Verify configuring CPU threads works and returns an integer thread count."""
        threads = configure_cpu_threads(2)
        assert threads == 2
        assert torch.get_num_threads() == 2

    def test_get_device_info(self) -> None:
        """Verify get_device_info reports CPU as selected device and is_using_cuda is False."""
        info = get_device_info()
        assert info["selected_device"] == "cpu"
        assert info["device_type"] == "cpu"
        assert info["is_using_cuda"] is False
        assert isinstance(info["num_cpu_threads"], int)
        assert "pytorch_version" in info

    def test_tensor_creation_on_cpu(self) -> None:
        """Verify tensor arithmetic functions properly on the resolved CPU device."""
        device = resolve_device()
        t = torch.tensor([1.0, 2.0, 3.0], device=device)
        assert t.device.type == "cpu"
        assert (t * 2).sum().item() == 12.0
