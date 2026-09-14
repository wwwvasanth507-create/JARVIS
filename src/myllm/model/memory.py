"""
Memory Footprint and Resource Estimation for MyLLM Models.

Provides realistic estimates of RAM requirements for model parameters,
AdamW optimizer states, gradients, and forward/backward activations on CPU.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional
from myllm.config import ModelConfig


def format_bytes(num_bytes: int | float) -> str:
    """Format byte count into human-readable unit string."""
    units = ["B", "KB", "MB", "GB", "TB"]
    val = float(num_bytes)
    for unit in units:
        if abs(val) < 1024.0 or unit == "TB":
            return f"{val:.2f} {unit}"
        val /= 1024.0
    return f"{val:.2f} TB"


@dataclass
class ModelMemoryEstimate:
    """Detailed memory budget estimates for training and inference."""
    total_parameters: int
    trainable_parameters: int
    bytes_per_param: int
    parameter_memory_bytes: int
    parameter_memory_str: str
    optimizer_memory_bytes: int
    optimizer_memory_str: str
    gradient_memory_bytes: int
    gradient_memory_str: str
    activation_memory_bytes: int
    activation_memory_str: str
    total_training_memory_bytes: int
    total_training_memory_str: str
    inference_memory_bytes: int
    inference_memory_str: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def estimate_memory_footprint(
    config: ModelConfig,
    batch_size: int = 4,
    sequence_length: Optional[int] = None,
) -> ModelMemoryEstimate:
    """
    Estimate memory requirements for a model configuration under CPU execution.

    Estimates:
    - FP32 parameters: 4 bytes per parameter.
    - AdamW optimizer state: 8 bytes per trainable parameter (momentum + variance).
    - FP32 gradients: 4 bytes per trainable parameter.
    - Activation memory: intermediate tensors per layer (self-attention + MLP).

    Args:
        config: ModelConfig instance defining architecture dimensions.
        batch_size: Training batch size (or micro-batch size).
        sequence_length: Sequence length (defaults to config.context_length).

    Returns:
        ModelMemoryEstimate dataclass with detailed breakdowns.
    """
    seq_len = sequence_length or config.context_length
    vocab = config.vocab_size
    n_embd = config.n_embd
    n_layer = config.n_layer

    # 1. Parameter counts
    # Embeddings: wte (vocab * n_embd) + wpe (context_length * n_embd)
    wte_params = vocab * n_embd
    wpe_params = config.context_length * n_embd

    # Per block:
    # ln_1 (2 * n_embd), c_attn (n_embd * 3 * n_embd + 3 * n_embd if bias),
    # c_proj (n_embd * n_embd + n_embd if bias),
    # ln_2 (2 * n_embd), mlp.c_fc (n_embd * 4 * n_embd + 4 * n_embd),
    # mlp.c_proj (4 * n_embd * n_embd + n_embd)
    bias_term = 1 if config.bias else 0
    attn_params = (n_embd * 3 * n_embd + 3 * n_embd * bias_term) + (n_embd * n_embd + n_embd * bias_term)
    mlp_params = (n_embd * 4 * n_embd + 4 * n_embd * bias_term) + (4 * n_embd * n_embd + n_embd * bias_term)
    ln_params = 4 * n_embd  # ln_1 and ln_2
    block_params = attn_params + mlp_params + ln_params

    # Final ln_f (2 * n_embd)
    ln_f_params = 2 * n_embd

    # LM head: if tied, 0 new parameters; if untied, vocab * n_embd
    head_params = 0 if config.weight_tying else vocab * n_embd

    total_params = wte_params + wpe_params + (n_layer * block_params) + ln_f_params + head_params
    trainable_params = total_params

    # 2. Memory in bytes (FP32)
    bytes_per_param = 4
    param_bytes = total_params * bytes_per_param

    # Optimizer: AdamW tracks m (fp32) and v (fp32) -> 8 bytes per trainable param
    opt_bytes = trainable_params * 8

    # Gradients: 4 bytes per trainable param
    grad_bytes = trainable_params * 4

    # Activation memory estimation (per layer forward/backward storage):
    # - Attention Q, K, V: 3 * B * T * D
    # - Attention matrix: B * H * T * T
    # - Attention output: B * T * D
    # - MLP hidden: B * T * 4D
    # - MLP output: B * T * D
    # - Residuals and LayerNorms: ~4 * B * T * D
    acts_per_layer = (
        (3 * batch_size * seq_len * n_embd)
        + (batch_size * config.n_head * seq_len * seq_len)
        + (batch_size * seq_len * n_embd)
        + (batch_size * seq_len * 4 * n_embd)
        + (batch_size * seq_len * n_embd)
        + (4 * batch_size * seq_len * n_embd)
    ) * bytes_per_param
    activation_bytes = acts_per_layer * n_layer

    total_train_bytes = param_bytes + opt_bytes + grad_bytes + activation_bytes
    inference_bytes = param_bytes + (activation_bytes // 2)

    return ModelMemoryEstimate(
        total_parameters=total_params,
        trainable_parameters=trainable_params,
        bytes_per_param=bytes_per_param,
        parameter_memory_bytes=param_bytes,
        parameter_memory_str=format_bytes(param_bytes),
        optimizer_memory_bytes=opt_bytes,
        optimizer_memory_str=format_bytes(opt_bytes),
        gradient_memory_bytes=grad_bytes,
        gradient_memory_str=format_bytes(grad_bytes),
        activation_memory_bytes=activation_bytes,
        activation_memory_str=format_bytes(activation_bytes),
        total_training_memory_bytes=total_train_bytes,
        total_training_memory_str=format_bytes(total_train_bytes),
        inference_memory_bytes=inference_bytes,
        inference_memory_str=format_bytes(inference_bytes),
    )
