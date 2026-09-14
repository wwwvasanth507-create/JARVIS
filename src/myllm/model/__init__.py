"""
GPT-style Decoder-Only Transformer Language Model architecture for MyLLM.

Built from scratch using PyTorch CPU primitives with Pre-LayerNorm,
causal multi-head self-attention, and optional weight tying.
"""

from myllm.model.attention import CausalSelfAttention
from myllm.model.block import TransformerBlock
from myllm.model.gpt import GPTModel
from myllm.model.mlp import MLP
from myllm.model.utils import count_parameters, get_model_summary

__all__ = [
    "GPTModel",
    "TransformerBlock",
    "CausalSelfAttention",
    "MLP",
    "count_parameters",
    "get_model_summary",
]
