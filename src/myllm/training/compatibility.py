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
from pathlib import Path
from typing import Any, Dict, Optional, Union
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


def validate_sft_compatibility(
    model: nn.Module,
    checkpoint_path: Union[str, Path],
    tokenizer: Tokenizer,
    instruction_dataset: Any,
    config: Optional[AppConfig] = None,
) -> Dict[str, Any]:
    """
    Validate base model checkpoint and instruction dataset compatibility for SFT.

    Verifies:
    - Base checkpoint exists and contains valid model weights and config.
    - Model architecture in checkpoint matches active model instance.
    - Tokenizer fingerprint matches checkpoint.
    - Context length is sufficient for instruction dataset.
    - CPU device is strictly enforced.

    Returns:
        Loaded checkpoint payload dictionary.
    """
    ckpt_file = Path(checkpoint_path)
    if not ckpt_file.is_file():
        raise CompatibilityError(f"Base model checkpoint not found at: {ckpt_file}")

    try:
        payload = torch.load(ckpt_file, map_location="cpu", weights_only=False)
    except Exception as e:
        raise CompatibilityError(f"Failed to load base checkpoint from {ckpt_file}: {e}")

    # 1. CPU Device Verification
    for name, param in model.named_parameters():
        if param.device.type != "cpu":
            raise CompatibilityError(
                f"Model parameter '{name}' is on device '{param.device.type}'. "
                f"SFT strictly requires CPU execution."
            )

    # 2. Tokenizer Fingerprint Matching
    tok_fp = compute_tokenizer_fingerprint(tokenizer)
    ckpt_tok_fp = payload.get("tokenizer_fingerprint")
    if ckpt_tok_fp and tok_fp != ckpt_tok_fp:
        raise CompatibilityError(
            f"Tokenizer fingerprint mismatch! Checkpoint requires '{ckpt_tok_fp}', "
            f"but active tokenizer has '{tok_fp}'."
        )

    # 3. Model Architecture Matching
    model_cfg: Optional[ModelConfig] = getattr(model, "config", None)
    ckpt_cfg_dict = payload.get("config", {}).get("model", {})
    if model_cfg is not None and ckpt_cfg_dict:
        if model_cfg.vocab_size != ckpt_cfg_dict.get("vocab_size"):
            raise CompatibilityError(
                f"Vocab size mismatch between model ({model_cfg.vocab_size}) and "
                f"checkpoint ({ckpt_cfg_dict.get('vocab_size')})."
            )
        if model_cfg.n_embd != ckpt_cfg_dict.get("n_embd"):
            raise CompatibilityError(
                f"Embedding dimension mismatch between model ({model_cfg.n_embd}) and "
                f"checkpoint ({ckpt_cfg_dict.get('n_embd')})."
            )
        if model_cfg.n_layer != ckpt_cfg_dict.get("n_layer"):
            raise CompatibilityError(
                f"Layer count mismatch between model ({model_cfg.n_layer}) and "
                f"checkpoint ({ckpt_cfg_dict.get('n_layer')})."
            )
        if model_cfg.n_head != ckpt_cfg_dict.get("n_head"):
            raise CompatibilityError(
                f"Head count mismatch between model ({model_cfg.n_head}) and "
                f"checkpoint ({ckpt_cfg_dict.get('n_head')})."
            )

    # 4. Context Length Compatibility
    ds_seq_len = getattr(instruction_dataset, "sequence_length", None)
    if model_cfg is not None and ds_seq_len is not None:
        if ds_seq_len > model_cfg.context_length:
            raise CompatibilityError(
                f"Instruction dataset sequence_length ({ds_seq_len}) exceeds "
                f"model context_length ({model_cfg.context_length})."
            )

    logger.debug("SFT compatibility validation passed successfully.")
    return payload

