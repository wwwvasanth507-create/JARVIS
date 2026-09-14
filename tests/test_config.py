"""
Tests for configuration management system.
"""

from pathlib import Path
import pytest
from myllm.config import (
    AppConfig,
    LoggingConfig,
    ModelConfig,
    PathsConfig,
    SystemConfig,
    TrainingConfig,
    get_default_config,
    load_config,
)


class TestConfigSystem:
    def test_default_config_fields(self) -> None:
        """Verify default configuration has all required fields with sensible defaults."""
        config = get_default_config()

        # System fields
        assert config.system.seed == 42
        assert config.system.device == "cpu"
        assert config.system.num_threads == 4
        assert config.system.strict_cpu is True

        # Path fields
        assert config.paths.model_dir == "checkpoints"
        assert config.paths.checkpoint_dir == "checkpoints"
        assert config.paths.dataset_dir == "data"
        assert config.paths.log_dir == "logs"
        assert config.paths.experiment_dir == "experiments"

        # Model fields
        assert config.model.vocab_size == 1000
        assert config.model.context_length == 128
        assert config.model.n_layer == 4
        assert config.model.n_head == 4
        assert config.model.n_embd == 256
        assert config.model.activation == "gelu"
        assert config.model.bias is True

        # Training fields
        assert config.training.batch_size == 16
        assert config.training.learning_rate > 0

        # Logging fields
        assert config.logging.log_level == "INFO"

    def test_load_base_yaml(self) -> None:
        """Verify loading configs/base.yaml matches expected structure."""
        base_yaml = Path("configs/base.yaml")
        assert base_yaml.exists(), "configs/base.yaml must exist"

        config = load_config(base_yaml)
        assert config.system.device == "cpu"
        assert config.system.strict_cpu is True
        assert config.system.seed == 42
        assert config.paths.checkpoint_dir == "checkpoints"

    def test_strict_cpu_rejects_cuda_in_config(self) -> None:
        """Verify SystemConfig raises ValueError if device != 'cpu' under strict_cpu=True."""
        with pytest.raises(ValueError) as exc_info:
            SystemConfig(device="cuda", strict_cpu=True)
        assert "device must be 'cpu'" in str(exc_info.value)

    def test_model_config_head_divisibility_validation(self) -> None:
        """Verify ModelConfig validates that n_embd is divisible by n_head."""
        with pytest.raises(ValueError) as exc_info:
            ModelConfig(n_embd=100, n_head=6)
        assert "divisible" in str(exc_info.value)

    def test_paths_resolution(self, tmp_path: Path) -> None:
        """Verify resolving paths relative to a directory."""
        paths = PathsConfig(model_dir="custom_models")
        resolved = paths.resolve_paths(base_dir=tmp_path)
        assert resolved.model_dir == str(tmp_path / "custom_models")

    def test_yaml_roundtrip(self, tmp_path: Path) -> None:
        """Verify saving to and loading from a custom YAML file."""
        config = get_default_config()
        config.system.seed = 12345
        target = tmp_path / "custom.yaml"
        config.save_yaml(target)

        loaded = load_config(target)
        assert loaded.system.seed == 12345
