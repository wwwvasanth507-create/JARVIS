"""
Tests for reproducibility seeding and logging utilities.
"""

import logging
from pathlib import Path
import numpy as np
import torch
from myllm.utils.logging import get_logger
from myllm.utils.seed import set_seed


class TestUtils:
    def test_seed_reproducibility_torch(self) -> None:
        """Verify set_seed produces identical PyTorch random sequences on CPU."""
        set_seed(1337)
        t1 = torch.randn(10)

        set_seed(1337)
        t2 = torch.randn(10)

        assert torch.equal(t1, t2), "PyTorch CPU random sequences must match with same seed"

    def test_seed_reproducibility_numpy(self) -> None:
        """Verify set_seed produces identical NumPy random sequences."""
        set_seed(999)
        arr1 = np.random.randn(10)

        set_seed(999)
        arr2 = np.random.randn(10)

        np.testing.assert_array_equal(arr1, arr2)

    def test_get_logger_creation(self) -> None:
        """Verify logger instance creation and properties."""
        logger = get_logger("myllm_test", level=logging.DEBUG)
        assert logger.name == "myllm_test"
        assert logger.level == logging.DEBUG
        assert len(logger.handlers) >= 1

    def test_get_logger_file_output(self, tmp_path: Path) -> None:
        """Verify logger writes messages to specified log file."""
        log_file = tmp_path / "test.log"
        logger = get_logger("file_test", log_file=log_file, level=logging.INFO)
        test_msg = "CPU LLM Foundation Log Entry"
        logger.info(test_msg)

        # Flush handlers
        for handler in logger.handlers:
            handler.flush()

        assert log_file.exists()
        content = log_file.read_text(encoding="utf-8")
        assert test_msg in content
