"""
Configuration Management System for MyLLM.

Loads, validates, and serializes hierarchical configurations for system,
paths, model, training, and logging.
"""

from __future__ import annotations

import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional, Union
import yaml


@dataclass
class SystemConfig:
    """System and hardware execution settings."""
    seed: int = 42
    device: str = "cpu"
    num_threads: Optional[int] = 4
    strict_cpu: bool = True

    def __post_init__(self) -> None:
        if self.strict_cpu and self.device.lower().strip() != "cpu":
            raise ValueError(
                f"Invalid device '{self.device}'. When strict_cpu=True, device must be 'cpu'."
            )


@dataclass
class PathsConfig:
    """Directory paths for the project."""
    model_dir: str = "checkpoints"
    checkpoint_dir: str = "checkpoints"
    dataset_dir: str = "data"
    log_dir: str = "logs"
    experiment_dir: str = "experiments"

    def resolve_paths(self, base_dir: Optional[Union[str, Path]] = None) -> PathsConfig:
        """Resolve all path attributes relative to a base directory."""
        root = Path(base_dir) if base_dir else Path.cwd()
        return PathsConfig(
            model_dir=str(root / self.model_dir),
            checkpoint_dir=str(root / self.checkpoint_dir),
            dataset_dir=str(root / self.dataset_dir),
            log_dir=str(root / self.log_dir),
            experiment_dir=str(root / self.experiment_dir),
        )


@dataclass
class ModelConfig:
    """GPT-style decoder-only Transformer model dimensions and settings."""
    vocab_size: int = 1000
    context_length: int = 128
    n_layer: int = 4
    n_head: int = 4
    n_embd: int = 256
    dropout: float = 0.0
    bias: bool = True
    activation: str = "gelu"
    weight_tying: bool = True
    block_size: Optional[int] = None  # Backward compatibility alias for context_length

    def __post_init__(self) -> None:
        if self.block_size is not None and self.context_length == 128:
            self.context_length = self.block_size
        else:
            self.block_size = self.context_length

        if self.vocab_size <= 0:
            raise ValueError(f"vocab_size must be positive, got {self.vocab_size}")
        if self.context_length <= 0:
            raise ValueError(f"context_length must be positive, got {self.context_length}")
        if self.n_layer <= 0:
            raise ValueError(f"n_layer must be positive, got {self.n_layer}")
        if self.n_head <= 0:
            raise ValueError(f"n_head must be positive, got {self.n_head}")
        if self.n_embd <= 0:
            raise ValueError(f"n_embd must be positive, got {self.n_embd}")
        if self.n_embd % self.n_head != 0:
            raise ValueError(
                f"n_embd ({self.n_embd}) must be divisible by n_head ({self.n_head})."
            )
        if not (0.0 <= self.dropout < 1.0):
            raise ValueError(f"dropout must be in [0, 1), got {self.dropout}")
        if self.activation.lower() not in {"gelu", "relu", "silu", "tanh"}:
            raise ValueError(f"Unsupported activation '{self.activation}'. Supported: gelu, relu, silu, tanh.")

    @property
    def head_dim(self) -> int:
        """Dimension of each attention head."""
        return self.n_embd // self.n_head


@dataclass
class TrainingConfig:
    """Hyperparameters for model training."""
    batch_size: int = 16
    learning_rate: float = 6.0e-4
    min_learning_rate: float = 6.0e-5
    weight_decay: float = 0.1
    beta1: float = 0.9
    beta2: float = 0.95
    grad_clip: float = 1.0
    max_iters: int = 2000
    warmup_iters: int = 100
    eval_interval: int = 200
    eval_iters: int = 50
    save_interval: int = 500


@dataclass
class LoggingConfig:
    """Logging and telemetry settings."""
    log_level: str = "INFO"
    log_to_file: bool = True
    log_filename: str = "myllm.log"


@dataclass
class TokenizerConfig:
    """Byte-Level BPE Tokenizer hyperparameters and settings."""
    vocab_size: int = 1000
    min_pair_frequency: int = 2
    special_tokens: list[str] = field(
        default_factory=lambda: ["<PAD>", "<UNK>", "<BOS>", "<EOS>"]
    )
    max_documents: Optional[int] = None
    max_training_bytes: Optional[int] = None

    def __post_init__(self) -> None:
        if self.vocab_size < 260:
            raise ValueError(
                f"vocab_size ({self.vocab_size}) must be at least 260 to accommodate "
                f"the 4 special tokens and 256 base byte values."
            )
        if self.min_pair_frequency < 1:
            raise ValueError(
                f"min_pair_frequency ({self.min_pair_frequency}) must be at least 1."
            )


@dataclass
class AppConfig:
    """Root configuration object containing all sub-configurations."""
    system: SystemConfig = field(default_factory=SystemConfig)
    paths: PathsConfig = field(default_factory=PathsConfig)
    model: ModelConfig = field(default_factory=ModelConfig)
    training: TrainingConfig = field(default_factory=TrainingConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    tokenizer: TokenizerConfig = field(default_factory=TokenizerConfig)

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration hierarchy into a nested dictionary."""
        return asdict(self)

    def save_yaml(self, path: Union[str, Path]) -> None:
        """Save configuration dictionary to a YAML file."""
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            yaml.safe_dump(self.to_dict(), f, sort_keys=False, default_flow_style=False)


def _deep_update(base: dict, update: dict) -> dict:
    """Recursively update a dictionary."""
    for key, value in update.items():
        if isinstance(value, dict) and key in base and isinstance(base[key], dict):
            _deep_update(base[key], value)
        else:
            base[key] = value
    return base


def load_config(config_path: Optional[Union[str, Path]] = None) -> AppConfig:
    """
    Load an AppConfig instance.

    If config_path is provided and points to an existing file, the YAML contents
    are parsed and merged over default values. If config_path is None, the function
    checks for 'configs/base.yaml' from the current working directory.

    Args:
        config_path: Optional file path to a YAML configuration file.

    Returns:
        Populated and validated AppConfig instance.
    """
    if config_path is None:
        candidate = Path("configs/base.yaml")
        if candidate.is_file():
            config_path = candidate

    raw_data: Dict[str, Any] = {}
    if config_path is not None:
        path = Path(config_path)
        if path.is_file():
            with open(path, "r", encoding="utf-8") as f:
                loaded = yaml.safe_load(f)
                if isinstance(loaded, dict):
                    raw_data = loaded

    system_dict = raw_data.get("system", {})
    paths_dict = raw_data.get("paths", {})
    model_dict = raw_data.get("model", {})
    training_dict = raw_data.get("training", {})
    logging_dict = raw_data.get("logging", {})
    tokenizer_dict = raw_data.get("tokenizer", {})

    return AppConfig(
        system=SystemConfig(**system_dict),
        paths=PathsConfig(**paths_dict),
        model=ModelConfig(**model_dict),
        training=TrainingConfig(**training_dict),
        logging=LoggingConfig(**logging_dict),
        tokenizer=TokenizerConfig(**tokenizer_dict),
    )


def get_default_config() -> AppConfig:
    """Return an AppConfig instance with default values."""
    return AppConfig()
