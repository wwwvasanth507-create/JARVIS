"""
Safe Checkpoint and Tokenizer Loading for MyLLM Inference.

Loads trained checkpoints, restores GPT models directly to CPU, validates
model configuration, and enforces tokenizer fingerprint compatibility.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union
import torch
from myllm.config import ModelConfig
from myllm.data.tokenizer_pipeline import compute_tokenizer_fingerprint
from myllm.model.gpt import GPTModel
from myllm.tokenizer import Tokenizer

logger = logging.getLogger(__name__)


def load_checkpoint_for_inference(
    checkpoint_path: Union[str, Path],
    tokenizer: Optional[Tokenizer] = None,
    model_config: Optional[ModelConfig] = None,
) -> Tuple[GPTModel, Dict[str, Any]]:
    """
    Safely load a trained MyLLM checkpoint for CPU inference.

    Args:
        checkpoint_path: Path to the .pt checkpoint file.
        tokenizer: Optional Tokenizer instance to validate against checkpoint metadata.
        model_config: Optional explicit ModelConfig (extracted from checkpoint if omitted).

    Returns:
        Tuple of (model, metadata_dict).

    Raises:
        FileNotFoundError: If checkpoint file does not exist.
        ValueError: If checkpoint format is invalid, missing weights, or tokenizer fingerprint mismatches.
        RuntimeError: If model is not loaded onto CPU.
    """
    path = Path(checkpoint_path)
    if not path.is_file():
        raise FileNotFoundError(f"Checkpoint file not found at: {path}")

    try:
        payload = torch.load(path, map_location="cpu", weights_only=False)
    except Exception as e:
        raise ValueError(f"Failed to load checkpoint at {path}. Corrupted file: {e}") from e

    if not isinstance(payload, dict):
        raise ValueError(f"Corrupt checkpoint at {path}: expected dictionary payload, got {type(payload)}")

    if "model_state_dict" not in payload:
        raise ValueError(f"Corrupt checkpoint at {path}: missing required key 'model_state_dict'")

    # 1. Resolve Model Configuration
    if model_config is None:
        cfg_dict = payload.get("config")
        if isinstance(cfg_dict, dict) and "model" in cfg_dict:
            model_dict = cfg_dict["model"]
            model_config = ModelConfig(**model_dict)
        elif isinstance(cfg_dict, dict) and "vocab_size" in cfg_dict:
            model_config = ModelConfig(**cfg_dict)
        else:
            raise ValueError(
                f"Checkpoint at {path} does not contain valid model configuration metadata. "
                f"Please provide an explicit model_config."
            )

    # 2. Instantiate Model and Load State Dict
    model = GPTModel(model_config)
    try:
        model.load_state_dict(payload["model_state_dict"])
    except Exception as e:
        raise ValueError(f"Failed to restore model weights from {path}: {e}") from e

    # 3. Ensure CPU Device and Eval Mode
    model.eval()
    device = next(model.parameters()).device
    if device.type != "cpu":
        raise RuntimeError(f"Strict CPU enforcement violated: model device is '{device.type}'.")

    # 4. Tokenizer Validation
    if tokenizer is not None:
        ckpt_fp = payload.get("tokenizer_fingerprint", "")
        if ckpt_fp:
            tok_fp = compute_tokenizer_fingerprint(tokenizer)
            if tok_fp != ckpt_fp:
                raise ValueError(
                    f"Tokenizer fingerprint mismatch! Checkpoint expects fingerprint '{ckpt_fp}', "
                    f"but provided tokenizer has fingerprint '{tok_fp}'."
                )
        else:
            logger.warning(
                f"Checkpoint {path} does not contain 'tokenizer_fingerprint'. "
                f"Skipping fingerprint validation for backward compatibility."
            )

        if len(tokenizer) != model_config.vocab_size:
            raise ValueError(
                f"Vocabulary size mismatch: tokenizer has {len(tokenizer)} tokens, "
                f"but model configuration expects vocab_size={model_config.vocab_size}."
            )

    logger.info(
        f"Successfully loaded model from {path} for CPU inference "
        f"(vocab_size={model_config.vocab_size}, context_length={model_config.context_length}, "
        f"n_layer={model_config.n_layer}, n_head={model_config.n_head}, n_embd={model_config.n_embd})."
    )
    return model, payload


def load_inference_system(
    checkpoint_path: Union[str, Path],
    tokenizer_path: Optional[Union[str, Path]] = None,
    model_config: Optional[ModelConfig] = None,
) -> Tuple[GPTModel, Optional[Tokenizer], Dict[str, Any]]:
    """
    Convenience loader for both model and tokenizer.

    Args:
        checkpoint_path: Path to the .pt checkpoint.
        tokenizer_path: Optional path to tokenizer.json.
        model_config: Optional ModelConfig.

    Returns:
        Tuple of (model, tokenizer, checkpoint_payload).
    """
    tokenizer: Optional[Tokenizer] = None
    if tokenizer_path is not None:
        tok_file = Path(tokenizer_path)
        if not tok_file.is_file():
            raise FileNotFoundError(f"Tokenizer file not found at: {tok_file}")
        tokenizer = Tokenizer.load(tok_file)

    model, payload = load_checkpoint_for_inference(
        checkpoint_path=checkpoint_path,
        tokenizer=tokenizer,
        model_config=model_config,
    )
    return model, tokenizer, payload
