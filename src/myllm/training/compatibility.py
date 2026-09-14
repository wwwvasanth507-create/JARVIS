"""
Pre-Training Compatibility Validation for MyLLM.

Enforces strict verification across:
- Tokenizer fingerprints vs Dataset metadata fingerprints.
- Dataset vocabulary size vs Model vocabulary size.
- Model context length vs Dataset sequence length.
- Checkpoint tokenizer fingerprint compatibility.
- Internal consistency of dataset metadata.
- Strict CPU tensor and device placement (zero CUDA/GPU tolerance).
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional
import torch
import torch.nn as nn
from myllm.config import AppConfig, ModelConfig
from myllm.data.dataset import TokenDataset
from myllm.data.metadata import DatasetMetadata
from myllm.data.tokenizer_pipeline import compute_tokenizer_fingerprint
from myllm.tokenizer import Tokenizer

logger = logging.getLogger(__name__)


class CompatibilityError(ValueError):
    """Raised when training components or artifacts are incompatible."""


def validate_training_compatibility(
    model: nn.Module,
    train_dataset: TokenDataset,
    val_dataset: Optional[TokenDataset] = None,
    tokenizer: Optional[Tokenizer] = None,
    dataset_metadata: Optional[DatasetMetadata] = None,
    config: Optional[AppConfig] = None,
    checkpoint_payload: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Validate mutual compatibility of all training components before training commences.

    Raises:
        CompatibilityError: If any architectural, device, or fingerprint mismatch is found.
    """
    # 1. Strict CPU Device Verification
    for name, param in model.named_parameters():
        if param.device.type != "cpu":
            raise CompatibilityError(
                f"Model parameter '{name}' is allocated on device '{param.device.type}'. "
                f"MyLLM strictly requires CPU execution."
            )

    if config is not None:
        if config.system.strict_cpu and config.system.device.lower().strip() != "cpu":
            raise CompatibilityError(
                f"Config specifies device='{config.system.device}', but strict_cpu is True."
            )

    # 2. Sequence Length vs Context Length
    model_cfg: Optional[ModelConfig] = getattr(model, "config", None)
    if model_cfg is not None:
        if train_dataset.sequence_length > model_cfg.context_length:
            raise CompatibilityError(
                f"Train dataset sequence_length ({train_dataset.sequence_length}) exceeds "
                f"model context_length ({model_cfg.context_length})."
            )
        if val_dataset is not None and val_dataset.sequence_length > model_cfg.context_length:
            raise CompatibilityError(
                f"Validation dataset sequence_length ({val_dataset.sequence_length}) exceeds "
                f"model context_length ({model_cfg.context_length})."
            )

    # 3. Vocabulary Size Compatibility
    if model_cfg is not None and tokenizer is not None:
        if len(tokenizer) != model_cfg.vocab_size:
            raise CompatibilityError(
                f"Vocabulary size mismatch: tokenizer has {len(tokenizer)} tokens, "
                f"but model configuration specifies vocab_size={model_cfg.vocab_size}."
            )

    # 4. Tokenizer Fingerprint vs Dataset Metadata
    if tokenizer is not None and dataset_metadata is not None:
        tok_fp = compute_tokenizer_fingerprint(tokenizer)
        if dataset_metadata.tokenizer_fingerprint and tok_fp != dataset_metadata.tokenizer_fingerprint:
            raise CompatibilityError(
                f"Tokenizer fingerprint mismatch! Tokenizer has fingerprint '{tok_fp}', "
                f"but dataset metadata requires '{dataset_metadata.tokenizer_fingerprint}'."
            )
        if dataset_metadata.tokenizer_vocab_size > 0 and len(tokenizer) != dataset_metadata.tokenizer_vocab_size:
            raise CompatibilityError(
                f"Dataset metadata expects tokenizer_vocab_size={dataset_metadata.tokenizer_vocab_size}, "
                f"but provided tokenizer has {len(tokenizer)} tokens."
            )

    # 5. Checkpoint Fingerprint Compatibility
    if checkpoint_payload is not None:
        ckpt_tok_fp = checkpoint_payload.get("tokenizer_fingerprint")
        if ckpt_tok_fp and tokenizer is not None:
            tok_fp = compute_tokenizer_fingerprint(tokenizer)
            if tok_fp != ckpt_tok_fp:
                raise CompatibilityError(
                    f"Checkpoint expects tokenizer fingerprint '{ckpt_tok_fp}', "
                    f"but active tokenizer has '{tok_fp}'."
                )

    # 6. Dataset Internal Consistency
    if dataset_metadata is not None:
        if dataset_metadata.total_tokens != (dataset_metadata.train_tokens + dataset_metadata.validation_tokens):
            raise CompatibilityError(
                f"Dataset metadata is internally inconsistent: total_tokens ({dataset_metadata.total_tokens}) "
                f"!= train_tokens ({dataset_metadata.train_tokens}) + "
                f"validation_tokens ({dataset_metadata.validation_tokens})."
            )

    logger.debug("Pre-training compatibility validation passed successfully.")
