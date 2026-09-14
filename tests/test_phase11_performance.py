"""
Test Suite for Phase 11: CPU Performance Optimization, Profiling & Engineering.

Validates:
1. CPU thread configuration and persistence
2. Model weight tying integrity (wte.weight is lm_head.weight)
3. Inference mode vs no_grad mathematical equivalence
4. Attention optimization equivalence (F.scaled_dot_product_attention vs manual mask)
5. KV cache incremental forward equivalence with un-cached forward (tolerance <= 1e-4)
6. Deterministic greedy generation equivalence (cached vs naive)
7. Deterministic seeded sampling generation equivalence
8. Tokenizer chunk-cache equivalence, deterministic IDs, and lossless Unicode round-trip
9. Data pipeline batching preallocation correctness and tensor shapes
10. Environment info & CPU specs
11. Benchmark result comparison logic and regression thresholds
"""

from __future__ import annotations

from pathlib import Path
import tempfile
import numpy as np
import pytest
import torch
import torch.nn.functional as F

from myllm.config import ModelConfig
from myllm.data.batching import BatchGenerator
from myllm.data.dataset import TokenDataset
from myllm.inference import GenerationConfig, Generator
from myllm.inference.cache import KVCache
from myllm.model.attention import CausalSelfAttention
from myllm.model.gpt import GPTModel
from myllm.tokenizer import Tokenizer
from scripts.benchmark_suite import get_environment_info
from scripts.compare_benchmarks import calc_change, compare_benchmarks


@pytest.fixture
def small_model_and_tokenizer():
    tok_path = Path("checkpoints/smoke/tokenizer.json")
    if not tok_path.is_file():
        tok_path = Path("data/tokenized/tokenizer.json")
    if tok_path.is_file():
        tokenizer = Tokenizer.load(tok_path)
    else:
        tokenizer = Tokenizer()

    config = ModelConfig(
        vocab_size=len(tokenizer),
        context_length=64,
        n_layer=2,
        n_head=2,
        n_embd=32,
    )
    torch.manual_seed(42)
    model = GPTModel(config)
    model.eval()
    return model, tokenizer, config


def test_cpu_thread_configuration():
    """Verify PyTorch CPU thread count can be queried and set cleanly."""
    initial_threads = torch.get_num_threads()
    assert initial_threads >= 1

    try:
        torch.set_num_threads(2)
        assert torch.get_num_threads() == 2
        torch.set_num_threads(1)
        assert torch.get_num_threads() == 1
    finally:
        torch.set_num_threads(initial_threads)


def test_weight_tying_integrity(small_model_and_tokenizer):
    """Verify embedding weights and LM head weights are strictly identical shared tensors."""
    model, _, _ = small_model_and_tokenizer
    assert model.lm_head.weight is model.transformer.wte.weight
    assert model.transformer.wte.weight.data_ptr() == model.lm_head.weight.data_ptr()

    # Both names should exist in the module graph
    param_names = [name for name, _ in model.named_parameters(remove_duplicate=False)]
    assert "transformer.wte.weight" in param_names
    assert "lm_head.weight" in param_names


def test_inference_mode_vs_no_grad(small_model_and_tokenizer):
    """Verify torch.inference_mode produces identical logits to torch.no_grad."""
    model, _, _ = small_model_and_tokenizer
    x = torch.randint(0, model.config.vocab_size, (2, 16), dtype=torch.long)

    with torch.no_grad():
        out_no_grad, _ = model(x)

    with torch.inference_mode():
        out_inf_mode, _ = model(x)

    max_diff = torch.max(torch.abs(out_no_grad - out_inf_mode)).item()
    assert max_diff == 0.0, f"Expected identical logits, got max diff {max_diff}"


def test_attention_optimization_equivalence():
    """Verify CausalSelfAttention scaled_dot_product_attention path matches manual formula."""
    config = ModelConfig(
        vocab_size=100,
        context_length=32,
        n_layer=1,
        n_head=2,
        n_embd=16,
    )
    torch.manual_seed(123)
    attn = CausalSelfAttention(config)
    attn.eval()

    B, T, C = 2, 8, 16
    x = torch.randn(B, T, C)

    with torch.inference_mode():
        # Standard forward using F.scaled_dot_product_attention
        out_optimized = attn(x)

        # Manual attention calculation using causal mask buffer
        q, k, v = attn.c_attn(x).split(attn.n_embd, dim=2)
        head_dim = attn.head_dim
        k = k.view(B, T, attn.n_head, head_dim).transpose(1, 2)
        q = q.view(B, T, attn.n_head, head_dim).transpose(1, 2)
        v = v.view(B, T, attn.n_head, head_dim).transpose(1, 2)

        att = (q @ k.transpose(-2, -1)) * (1.0 / np.sqrt(head_dim))
        att = att.masked_fill(attn.causal_mask[:, :, :T, :T] == 0, float("-inf"))
        att = F.softmax(att, dim=-1)
        manual_out = att @ v
        manual_out = manual_out.transpose(1, 2).contiguous().view(B, T, C)
        manual_out = attn.c_proj(manual_out)

    max_diff = torch.max(torch.abs(out_optimized - manual_out)).item()
    assert max_diff < 1e-5, f"Attention output differs from manual calculation by {max_diff}"


def test_kv_cache_forward_equivalence(small_model_and_tokenizer):
    """Verify incremental KV cache forward matches full un-cached forward within tolerance <= 1e-4."""
    model, _, _ = small_model_and_tokenizer
    seq_len = 12
    x = torch.randint(0, model.config.vocab_size, (1, seq_len), dtype=torch.long)

    # Full forward
    with torch.inference_mode():
        full_logits = model(x)
        expected_last_logits = full_logits[:, -1, :]

    # Incremental forward with KV cache
    cache = KVCache(context_length=model.config.context_length)

    with torch.inference_mode():
        # Step through tokens one by one
        for t in range(seq_len):
            step_input = x[:, t : t + 1]
            step_logits, present_kvs = model(
                step_input,
                past_key_values=cache.past_key_values,
                use_cache=True,
            )
            cache.update(present_kvs)

    incremental_last_logits = step_logits[:, -1, :]
    max_diff = torch.max(torch.abs(expected_last_logits - incremental_last_logits)).item()
    assert max_diff < 1e-4, f"KV cache logit difference {max_diff} exceeded tolerance 1e-4"


def test_deterministic_greedy_generation_equivalence(small_model_and_tokenizer):
    """Verify greedy generation produces identical token IDs with and without KV cache."""
    model, tokenizer, _ = small_model_and_tokenizer
    generator = Generator(model, tokenizer)
    prompt = "Test deterministic output"

    # Uncached generation
    cfg_naive = GenerationConfig(max_new_tokens=10, temperature=1.0, top_k=0, do_sample=False, use_cache=False)
    result_naive = generator.generate(prompt, cfg_naive)

    # Cached generation
    cfg_cached = GenerationConfig(max_new_tokens=10, temperature=1.0, top_k=0, do_sample=False, use_cache=True)
    result_cached = generator.generate(prompt, cfg_cached)

    assert result_naive.generated_token_ids == result_cached.generated_token_ids
    assert result_naive.text == result_cached.text


def test_deterministic_seeded_sampling_equivalence(small_model_and_tokenizer):
    """Verify seeded sampling produces identical token sequences across repeated runs."""
    model, tokenizer, _ = small_model_and_tokenizer
    generator = Generator(model, tokenizer)
    prompt = "Sampling reproducibility"
    gen_config = GenerationConfig(max_new_tokens=10, temperature=0.8, top_k=10, do_sample=True, seed=42, use_cache=True)

    run1 = generator.generate(prompt, gen_config)
    run2 = generator.generate(prompt, gen_config)

    assert run1.generated_token_ids == run2.generated_token_ids
    assert run1.text == run2.text


def test_tokenizer_caching_and_lossless_roundtrip(small_model_and_tokenizer):
    """Verify tokenizer chunk cache returns exact deterministic IDs and lossless decode."""
    _, tokenizer, _ = small_model_and_tokenizer
    test_texts = [
        "Hello world! This is a test of the optimized tokenizer chunk caching.",
        "Short text.",
        "Special tokens: <|im_start|>user\nHello<|im_end|>\n<|im_start|>assistant\nHi!<|im_end|>",
        "Tamil text: வணக்கம் உலகம்! எப்படி இருக்கிறீர்கள்?",
        "Numbers and symbols: 12345 + 67890 = 80235, @#$%^&*()_+-=",
    ]

    for text in test_texts:
        # First encode (populates cache)
        ids1 = tokenizer.encode(text)
        # Second encode (hits cache)
        ids2 = tokenizer.encode(text)
        assert ids1 == ids2, f"Tokenizer IDs not deterministic for: {text}"

        # Decode
        decoded = tokenizer.decode(ids1)
        assert decoded == text, f"Lossless round-trip failed!\nOriginal: {text}\nDecoded:  {decoded}"


def test_data_batching_preallocated_buffers():
    """Verify BatchGenerator preallocated buffers create valid, contiguous tensors with exact shapes."""
    seq_len = 8
    batch_size = 4
    train_bin = Path("data/tokenized/train.bin")
    if not train_bin.is_file():
        pytest.skip("data/tokenized/train.bin not found")

    dataset = TokenDataset(train_bin, sequence_length=seq_len, allow_cross_document_sequences=True)
    assert len(dataset) > batch_size

    bg = BatchGenerator(dataset, batch_size=batch_size, shuffle=False)
    batch = next(iter(bg))
    x, y = batch

    assert isinstance(x, torch.Tensor)
    assert isinstance(y, torch.Tensor)
    assert x.shape == (batch_size, seq_len)
    assert y.shape == (batch_size, seq_len)
    assert x.dtype == torch.long
    assert y.dtype == torch.long
    assert x.is_contiguous()
    assert y.is_contiguous()

    # Verify target is input shifted by 1
    for b in range(batch_size):
        np.testing.assert_array_equal(x[b, 1:].numpy(), y[b, :-1].numpy())


def test_environment_info():
    """Verify get_environment_info returns valid CPU and thread hardware info."""
    env = get_environment_info()
    assert "cpu_hardware" in env
    assert "default_intraop_threads" in env
    assert env["cpu_hardware"]["logical_cores"] >= 1
    assert env["cuda_available"] is False or isinstance(env["cuda_available"], bool)
    assert env["is_using_cuda"] is False


def test_benchmark_serialization_and_regression_guard():
    """Verify compare_benchmarks parses valid JSON metrics and checks thresholds."""
    baseline = {
        "forward_benchmarks": [
            {"batch_size": 1, "sequence_length": 64, "mean_latency_ms": 2.50, "tokens_per_second": 400.0}
        ],
        "inference_kv_cache": {
            "prefill_latency_ms": 5.0,
            "first_token_latency_ms": 6.0,
            "naive_tokens_per_sec": 40.0,
            "cached_tokens_per_sec": 80.0,
            "kv_cache_speedup": 2.0,
        },
    }
    current_improved = {
        "forward_benchmarks": [
            {"batch_size": 1, "sequence_length": 64, "mean_latency_ms": 1.25, "tokens_per_second": 800.0}
        ],
        "inference_kv_cache": {
            "prefill_latency_ms": 3.0,
            "first_token_latency_ms": 4.0,
            "naive_tokens_per_sec": 50.0,
            "cached_tokens_per_sec": 120.0,
            "kv_cache_speedup": 2.4,
        },
    }
    current_regressed = {
        "forward_benchmarks": [
            {"batch_size": 1, "sequence_length": 64, "mean_latency_ms": 5.00, "tokens_per_second": 200.0}
        ],
        "inference_kv_cache": {
            "prefill_latency_ms": 10.0,
            "first_token_latency_ms": 12.0,
            "naive_tokens_per_sec": 20.0,
            "cached_tokens_per_sec": 40.0,
            "kv_cache_speedup": 2.0,
        },
    }

    # Improved run
    rows_imp, has_reg_imp, md_imp = compare_benchmarks(baseline, current_improved, threshold_pct=10.0)
    assert has_reg_imp is False
    assert any(r["status"] == "IMPROVED" for r in rows_imp)
    assert "| Metric | Baseline | Current | Delta | % Change | Status |" in md_imp

    # Regressed run
    rows_reg, has_reg_reg, md_reg = compare_benchmarks(baseline, current_regressed, threshold_pct=10.0)
    assert has_reg_reg is True
    assert any(r["status"] == "REGRESSED" for r in rows_reg)

    # calc_change helper
    d, pct, status = calc_change(100.0, 50.0, higher_is_better=False)
    assert d == -50.0
    assert pct == -50.0
    assert status == "IMPROVED"
