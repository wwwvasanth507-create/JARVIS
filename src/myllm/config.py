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
    """Hyperparameters and runtime settings for model training on CPU."""
    batch_size: int = 4
    max_steps: int = 100
    epochs: Optional[int] = None
    learning_rate: float = 0.0003
    min_learning_rate: float = 0.00003
    weight_decay: float = 0.1
    beta1: float = 0.9
    beta2: float = 0.95
    eps: float = 1e-8
    grad_clip_norm: float = 1.0
    warmup_steps: int = 10
    log_every_steps: int = 10
    eval_every_steps: int = 50
    eval_batches: int = 10
    checkpoint_every_steps: int = 50
    max_checkpoints: int = 3
    seed: int = 42
    gradient_accumulation_steps: int = 1
    save_best: bool = True
    resume_from: Optional[str] = None
    num_workers: int = 0

    # Backward-compatibility aliases
    max_iters: Optional[int] = None
    warmup_iters: Optional[int] = None
    grad_clip: Optional[float] = None
    eval_interval: Optional[int] = None
    eval_iters: Optional[int] = None
    save_interval: Optional[int] = None

    def __post_init__(self) -> None:
        # Sync backward compatibility aliases
        if self.max_iters is not None and self.max_steps == 100:
            self.max_steps = self.max_iters
        else:
            self.max_iters = self.max_steps

        if self.warmup_iters is not None and self.warmup_steps == 10:
            self.warmup_steps = self.warmup_iters
        else:
            self.warmup_iters = self.warmup_steps

        if self.grad_clip is not None and self.grad_clip_norm == 1.0:
            self.grad_clip_norm = self.grad_clip
        else:
            self.grad_clip = self.grad_clip_norm

        if self.eval_interval is not None and self.eval_every_steps == 50:
            self.eval_every_steps = self.eval_interval
        else:
            self.eval_interval = self.eval_every_steps

        if self.eval_iters is not None and self.eval_batches == 10:
            self.eval_batches = self.eval_iters
        else:
            self.eval_iters = self.eval_batches

        if self.save_interval is not None and self.checkpoint_every_steps == 50:
            self.checkpoint_every_steps = self.save_interval
        else:
            self.save_interval = self.checkpoint_every_steps

        # Validations
        if self.batch_size <= 0:
            raise ValueError(f"batch_size must be positive, got {self.batch_size}")
        if self.max_steps <= 0:
            raise ValueError(f"max_steps must be positive, got {self.max_steps}")
        if self.learning_rate <= 0:
            raise ValueError(f"learning_rate must be positive, got {self.learning_rate}")
        if self.min_learning_rate < 0:
            raise ValueError(f"min_learning_rate cannot be negative, got {self.min_learning_rate}")
        if self.min_learning_rate > self.learning_rate:
            raise ValueError(
                f"min_learning_rate ({self.min_learning_rate}) cannot exceed "
                f"learning_rate ({self.learning_rate})"
            )
        if self.weight_decay < 0:
            raise ValueError(f"weight_decay cannot be negative, got {self.weight_decay}")
        if not (0.0 <= self.beta1 < 1.0):
            raise ValueError(f"beta1 must be in [0, 1), got {self.beta1}")
        if not (0.0 <= self.beta2 < 1.0):
            raise ValueError(f"beta2 must be in [0, 1), got {self.beta2}")
        if self.eps <= 0:
            raise ValueError(f"eps must be positive, got {self.eps}")
        if self.grad_clip_norm <= 0:
            raise ValueError(f"grad_clip_norm must be positive, got {self.grad_clip_norm}")
        if self.warmup_steps < 0:
            raise ValueError(f"warmup_steps cannot be negative, got {self.warmup_steps}")
        if self.warmup_steps > self.max_steps:
            raise ValueError(
                f"warmup_steps ({self.warmup_steps}) cannot exceed max_steps ({self.max_steps})"
            )
        if self.log_every_steps <= 0:
            raise ValueError(f"log_every_steps must be positive, got {self.log_every_steps}")
        if self.eval_every_steps <= 0:
            raise ValueError(f"eval_every_steps must be positive, got {self.eval_every_steps}")
        if self.eval_batches <= 0:
            raise ValueError(f"eval_batches must be positive, got {self.eval_batches}")
        if self.checkpoint_every_steps <= 0:
            raise ValueError(f"checkpoint_every_steps must be positive, got {self.checkpoint_every_steps}")
        if self.max_checkpoints <= 0:
            raise ValueError(f"max_checkpoints must be positive, got {self.max_checkpoints}")
        if self.gradient_accumulation_steps <= 0:
            raise ValueError(
                f"gradient_accumulation_steps must be positive, got {self.gradient_accumulation_steps}"
            )
        if self.epochs is not None and self.epochs <= 0:
            raise ValueError(f"epochs must be positive if specified, got {self.epochs}")



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
class DataConfig:
    """Dataset ingestion, tokenization, and binary cache settings."""
    input_path: str = "data/raw"
    output_path: str = "data/tokenized"
    validation_ratio: float = 0.1
    sequence_length: int = 128
    add_bos: bool = False
    add_eos: bool = True
    allow_cross_document_sequences: bool = False
    normalize_unicode: bool = False
    strip_bom: bool = True
    normalize_newlines: bool = True
    strip_outer_whitespace: bool = False
    recursive: bool = True
    extensions: list[str] = field(default_factory=lambda: [".txt", ".md", ".text"])
    seed: int = 42

    def __post_init__(self) -> None:
        if not (0.0 <= self.validation_ratio < 1.0):
            raise ValueError(
                f"validation_ratio must be in [0.0, 1.0), got {self.validation_ratio}"
            )
        if self.sequence_length <= 0:
            raise ValueError(
                f"sequence_length must be positive, got {self.sequence_length}"
            )


@dataclass
class InstructionConfig:
    """Supervised Instruction-Tuning (SFT) settings."""
    base_checkpoint: Optional[str] = None
    template_version: str = "1.0"
    mask_prompt_labels: bool = True
    supervise_eos: bool = True
    response_truncation_policy: str = "reject"  # "reject" or "truncate"
    eval_prompts_file: Optional[str] = None
    instruction_data_path: str = "data/instruction"


@dataclass
class ServerConfig:
    """Local API server and serving configuration."""
    host: str = "127.0.0.1"
    port: int = 8000
    device: str = "cpu"
    checkpoint: str = "experiments/phase7/phase7_sft_run/checkpoints/best.pt"
    tokenizer: str = "data/tokenized/tokenizer.json"
    max_sessions: int = 100
    max_message_length: int = 4096
    max_new_tokens: int = 128
    default_temperature: float = 0.7
    default_top_p: float = 0.9
    cors_origins: list[str] = field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ]
    )

    def __post_init__(self) -> None:
        if self.device.lower().strip() != "cpu":
            raise ValueError(f"ServerConfig strictly requires device='cpu', got '{self.device}'.")
        if self.port <= 0 or self.port > 65535:
            raise ValueError(f"Invalid server port: {self.port}.")
        if self.max_sessions <= 0:
            raise ValueError(f"max_sessions must be positive, got {self.max_sessions}.")


@dataclass
class AppConfig:
    """Root configuration object containing all sub-configurations."""
    system: SystemConfig = field(default_factory=SystemConfig)
    paths: PathsConfig = field(default_factory=PathsConfig)
    model: ModelConfig = field(default_factory=ModelConfig)
    training: TrainingConfig = field(default_factory=TrainingConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    tokenizer: TokenizerConfig = field(default_factory=TokenizerConfig)
    data: DataConfig = field(default_factory=DataConfig)
    instruction: InstructionConfig = field(default_factory=InstructionConfig)
    server: ServerConfig = field(default_factory=ServerConfig)

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


def resolve_config_path(config_path: Optional[Union[str, Path]] = None) -> Optional[Path]:
    """Resolve configuration file path or named profile to an existing Path."""
    if config_path is None:
        candidate = Path("configs/base.yaml")
        return candidate if candidate.is_file() else None

    path = Path(config_path)
    if path.is_file():
        return path

    # Check named profiles under configs/profiles/ and configs/instruction/
    name = str(config_path).strip()
    profile_candidates = [
        Path(f"configs/profiles/{name}.yaml"),
        Path(f"configs/profiles/{name}"),
        Path(f"configs/instruction/{name}.yaml"),
        Path(f"configs/instruction/{name}"),
        Path(f"configs/{name}.yaml"),
        Path(f"configs/{name}"),
    ]
    for cand in profile_candidates:
        if cand.is_file():
            return cand

    return None


def load_config(config_path: Optional[Union[str, Path]] = None) -> AppConfig:
    """
    Load an AppConfig instance from a YAML file or named profile.

    Supports:
    - Direct file paths (e.g. 'configs/base.yaml', 'configs/profiles/small_cpu.yaml').
    - Named profiles (e.g. 'tiny_cpu', 'small_cpu', 'medium_cpu', 'tiny_sft').
    - None (defaults to 'configs/base.yaml').

    Args:
        config_path: Optional file path or profile name.

    Returns:
        Populated and validated AppConfig instance.
    """
    resolved_path = resolve_config_path(config_path)
    raw_data: Dict[str, Any] = {}

    if resolved_path is not None and resolved_path.is_file():
        with open(resolved_path, "r", encoding="utf-8") as f:
            loaded = yaml.safe_load(f)
            if isinstance(loaded, dict):
                raw_data = loaded

    system_dict = raw_data.get("system", {})
    paths_dict = raw_data.get("paths", {})
    model_dict = raw_data.get("model", {})
    training_dict = raw_data.get("training", {})
    logging_dict = raw_data.get("logging", {})
    tokenizer_dict = raw_data.get("tokenizer", {})
    data_dict = raw_data.get("data", {})
    instruction_dict = raw_data.get("instruction", {})
    server_dict = raw_data.get("server", {})

    return AppConfig(
        system=SystemConfig(**system_dict),
        paths=PathsConfig(**paths_dict),
        model=ModelConfig(**model_dict),
        training=TrainingConfig(**training_dict),
        logging=LoggingConfig(**logging_dict),
        tokenizer=TokenizerConfig(**tokenizer_dict),
        data=DataConfig(**data_dict),
        instruction=InstructionConfig(**instruction_dict),
        server=ServerConfig(**server_dict),
    )


def load_profile(profile_name: str) -> AppConfig:
    """Load a named configuration profile (e.g. 'tiny_cpu', 'small_cpu', 'medium_cpu')."""
    resolved = resolve_config_path(profile_name)
    if resolved is None:
        raise FileNotFoundError(
            f"Configuration profile '{profile_name}' not found. "
            f"Searched in configs/profiles/{profile_name}.yaml and configs/."
        )
    return load_config(resolved)


def get_default_config() -> AppConfig:
    """Return an AppConfig instance with default values."""
    return AppConfig()
