"""
Comprehensive Test Suite for Phase 5: Inference, Sampling, KV Cache, and Evaluation.

Covers all 31 required verification points:
1. Generation config validation
2. Checkpoint loading
3. Tokenizer fingerprint validation
4. Greedy generation determinism
5. Temperature transformation
6. Top-k filtering
7. Top-p filtering
8. Repetition penalty
9. EOS stopping
10. Max token stopping
11. Context length enforcement
12. Deterministic generation with seed
13. Different seed behavior
14. Generation result structure
15. CPU inference verification
16. No CUDA usage
17. KV cache initialization
18. KV cache shape
19. KV cache growth
20. KV cache reset
21. Full forward vs cached forward logit equivalence
22. Cached vs naive generation token equivalence
23. Cache context overflow
24. Perplexity calculation
25. Token-weighted loss aggregation
26. Evaluation model.eval() behavior
27. Evaluation torch.no_grad() behavior
28. Evaluation metrics structure
29. CLI generation smoke test
30. CLI evaluation smoke test
31. Benchmark smoke test
32. Non-finite logit handling and numerical stability
"""

from __future__ import annotations

import math
import subprocess
import sys
from pathlib import Path
import pytest
import torch
import torch.nn as nn
import numpy as np
from myllm.config import AppConfig, ModelConfig
from myllm.data.dataset import TokenDataset
from myllm.data.metadata import DatasetMetadata
from myllm.data.tokenizer_pipeline import compute_tokenizer_fingerprint
from myllm.evaluation.evaluator import GenerationEvaluator
from myllm.evaluation.metrics import EvaluationMetrics, calculate_perplexity
from myllm.evaluation.perplexity import evaluate_perplexity
from myllm.inference.benchmark import benchmark_inference
from myllm.inference.cache import KVCache
from myllm.inference.generator import Generator
from myllm.inference.loader import load_checkpoint_for_inference, load_inference_system
from myllm.inference.sampling import (
    InferenceError,
    apply_repetition_penalty,
    apply_temperature,
    apply_top_k,
    apply_top_p,
    sample_next_token,
)
from myllm.inference.stopping import (
    ContextOverflowError,
    check_eos,
    validate_and_truncate_context,
)
from myllm.inference.types import GenerationConfig, GenerationResult
from myllm.model.gpt import GPTModel
from myllm.tokenizer import Tokenizer
from myllm.training.checkpoint import save_checkpoint
from myllm.training.scheduler import CosineWarmupScheduler
from myllm.training.state import TrainingState


@pytest.fixture
def small_config() -> ModelConfig:
    return ModelConfig(
        vocab_size=265,
        context_length=32,
        n_layer=2,
        n_head=2,
        n_embd=32,
    )


@pytest.fixture
def small_model(small_config: ModelConfig) -> GPTModel:
    torch.manual_seed(42)
    model = GPTModel(small_config)
    model.eval()
    return model


@pytest.fixture
def dummy_tokenizer(tmp_path: Path) -> Tokenizer:
    tok = Tokenizer.train(["hello world the test model token abc xyz"] * 10, vocab_size=265)
    tok_path = tmp_path / "tokenizer.json"
    tok.save(tok_path)
    return tok


# ---------------------------------------------------------------------------
# 1. Generation Config Validation
# ---------------------------------------------------------------------------
def test_generation_config_validation():
    cfg = GenerationConfig()
    assert cfg.max_new_tokens == 50
    assert cfg.temperature == 1.0

    with pytest.raises(ValueError, match="max_new_tokens must be positive"):
        GenerationConfig(max_new_tokens=0)

    with pytest.raises(ValueError, match="temperature must be positive"):
        GenerationConfig(temperature=-0.5)

    with pytest.raises(ValueError, match="top_k cannot be negative"):
        GenerationConfig(top_k=-1)

    with pytest.raises(ValueError, match="top_p must be in"):
        GenerationConfig(top_p=0.0)

    with pytest.raises(ValueError, match="repetition_penalty must be positive"):
        GenerationConfig(repetition_penalty=0.0)

    with pytest.raises(ValueError, match="Unsupported context_overflow_strategy"):
        GenerationConfig(context_overflow_strategy="invalid_strat")


# ---------------------------------------------------------------------------
# 2. Checkpoint Loading & 3. Tokenizer Fingerprint Validation
# ---------------------------------------------------------------------------
def test_checkpoint_loading_and_fingerprint_validation(tmp_path: Path, small_model: GPTModel, dummy_tokenizer: Tokenizer):
    app_cfg = AppConfig()
    app_cfg.model = small_model.config
    opt = torch.optim.AdamW(small_model.parameters(), lr=1e-3)
    sched = CosineWarmupScheduler(
        opt,
        learning_rate=1e-3,
        min_learning_rate=1e-4,
        warmup_steps=5,
        max_steps=20,
    )
    state = TrainingState(global_step=10, epoch=1, tokens_seen=500, val_loss=1.5)

    tok_fp = compute_tokenizer_fingerprint(dummy_tokenizer)
    ckpt_path = save_checkpoint(
        checkpoint_dir=tmp_path,
        model=small_model,
        optimizer=opt,
        scheduler=sched,
        state=state,
        config=app_cfg,
        tokenizer_fingerprint=tok_fp,
        dataset_fingerprint="dummy_data_fp",
    )

    # 1. Successful loading with matching tokenizer
    loaded_model, payload = load_checkpoint_for_inference(ckpt_path, tokenizer=dummy_tokenizer)
    assert isinstance(loaded_model, GPTModel)
    assert not loaded_model.training
    assert next(loaded_model.parameters()).device.type == "cpu"
    assert payload["tokenizer_fingerprint"] == tok_fp

    # 2. Mismatched tokenizer must fail clearly
    mismatched_tok = Tokenizer.train(["completely different corpus vocabulary words"] * 10, vocab_size=265)
    with pytest.raises(ValueError, match="Tokenizer fingerprint mismatch"):
        load_checkpoint_for_inference(ckpt_path, tokenizer=mismatched_tok)

    # 3. Missing file fails clearly
    with pytest.raises(FileNotFoundError):
        load_checkpoint_for_inference(tmp_path / "non_existent.pt")


# ---------------------------------------------------------------------------
# 4. Greedy Generation Determinism
# ---------------------------------------------------------------------------
def test_greedy_generation_determinism(small_model: GPTModel):
    generator = Generator(small_model, device="cpu")
    prompt = [1, 2, 3, 4]
    cfg = GenerationConfig(max_new_tokens=10, do_sample=False)

    res1 = generator.generate(prompt, cfg)
    res2 = generator.generate(prompt, cfg)

    assert res1.generated_token_ids == res2.generated_token_ids
    assert len(res1.generated_token_ids) == 10
    assert res1.stopped_reason == "max_tokens"


# ---------------------------------------------------------------------------
# 5. Temperature Transformation
# ---------------------------------------------------------------------------
def test_temperature_transformation():
    logits = torch.tensor([1.0, 2.0, 3.0])
    scaled_1 = apply_temperature(logits, 1.0)
    assert torch.equal(scaled_1, logits)

    scaled_half = apply_temperature(logits, 0.5)
    assert torch.allclose(scaled_half, torch.tensor([2.0, 4.0, 6.0]))

    scaled_two = apply_temperature(logits, 2.0)
    assert torch.allclose(scaled_two, torch.tensor([0.5, 1.0, 1.5]))


# ---------------------------------------------------------------------------
# 6. Top-K Filtering
# ---------------------------------------------------------------------------
def test_top_k_filtering():
    logits = torch.tensor([1.0, 5.0, 2.0, 8.0, 3.0])
    filtered = apply_top_k(logits, top_k=2)

    # Top 2 values are 8.0 (idx 3) and 5.0 (idx 1)
    assert filtered[3] == 8.0
    assert filtered[1] == 5.0
    assert filtered[0] == float("-inf")
    assert filtered[2] == float("-inf")
    assert filtered[4] == float("-inf")

    # top_k=0 disables
    disabled = apply_top_k(logits, top_k=0)
    assert torch.equal(disabled, logits)

    # top_k >= vocab_size preserves all
    all_k = apply_top_k(logits, top_k=100)
    assert torch.equal(all_k, logits)


# ---------------------------------------------------------------------------
# 7. Top-P / Nucleus Filtering
# ---------------------------------------------------------------------------
def test_top_p_filtering():
    # Probabilities: [0.5, 0.3, 0.15, 0.05]
    # Corresponding logits
    probs = torch.tensor([0.5, 0.3, 0.15, 0.05])
    logits = torch.log(probs)

    # top_p = 0.55 should keep top 2 tokens (0.5 + 0.3 = 0.8 >= 0.55)
    filtered = apply_top_p(logits, top_p=0.55)
    assert torch.isfinite(filtered[0])
    assert torch.isfinite(filtered[1])
    assert filtered[2] == float("-inf")
    assert filtered[3] == float("-inf")

    # top_p = 1.0 disables filtering
    disabled = apply_top_p(logits, top_p=1.0)
    assert torch.equal(disabled, logits)


# ---------------------------------------------------------------------------
# 8. Repetition Penalty
# ---------------------------------------------------------------------------
def test_repetition_penalty():
    logits = torch.tensor([2.0, -2.0, 4.0, -1.0])
    seen = [0, 1]
    penalty = 2.0

    penalized = apply_repetition_penalty(logits, seen, penalty)
    # Logit > 0: 2.0 / 2.0 = 1.0
    assert penalized[0].item() == 1.0
    # Logit < 0: -2.0 * 2.0 = -4.0
    assert penalized[1].item() == -4.0
    # Unseen tokens unchanged
    assert penalized[2].item() == 4.0
    assert penalized[3].item() == -1.0

    # penalty=1.0 is no-op
    nop = apply_repetition_penalty(logits, seen, 1.0)
    assert torch.equal(nop, logits)


# ---------------------------------------------------------------------------
# 9. EOS Stopping & 10. Max Token Stopping
# ---------------------------------------------------------------------------
def test_eos_and_max_token_stopping(small_model: GPTModel):
    generator = Generator(small_model, device="cpu")
    prompt = [1, 2, 3]

    # Max tokens stopping
    cfg_max = GenerationConfig(max_new_tokens=5, do_sample=False, stop_on_eos=False)
    res_max = generator.generate(prompt, cfg_max)
    assert len(res_max.generated_token_ids) == 5
    assert res_max.stopped_reason == "max_tokens"
    assert not res_max.stopped_on_eos

    # EOS stopping: designate the very first predicted token as EOS
    first_tok = res_max.generated_token_ids[0]
    cfg_eos = GenerationConfig(max_new_tokens=10, do_sample=False, stop_on_eos=True, eos_token_id=first_tok)
    res_eos = generator.generate(prompt, cfg_eos)
    assert len(res_eos.generated_token_ids) == 1
    assert res_eos.generated_token_ids[0] == first_tok
    assert res_eos.stopped_on_eos is True
    assert res_eos.stopped_reason == "eos"


# ---------------------------------------------------------------------------
# 11. Context Length Enforcement & Truncation
# ---------------------------------------------------------------------------
def test_context_length_enforcement():
    context_length = 10
    prompt = [1, 2, 3, 4, 5, 6, 7]  # 7 tokens
    max_new = 5  # 7 + 5 = 12 > 10

    # Strategy 'error' must raise ContextOverflowError
    with pytest.raises(ContextOverflowError):
        validate_and_truncate_context(prompt, max_new, context_length, strategy="error")

    # Strategy 'truncate_prompt' drops oldest prompt tokens from the left
    trunc_prompt, eff_max_new = validate_and_truncate_context(
        prompt, max_new, context_length, strategy="truncate_prompt"
    )
    assert len(trunc_prompt) + eff_max_new <= context_length
    assert trunc_prompt == [3, 4, 5, 6, 7]  # Preserves rightmost 5 tokens
    assert eff_max_new == 5


# ---------------------------------------------------------------------------
# 12. Deterministic Generation with Seed & 13. Seed Variation
# ---------------------------------------------------------------------------
def test_deterministic_generation_with_seed(small_model: GPTModel):
    generator = Generator(small_model, device="cpu")
    prompt = [5, 10, 15]
    cfg_seed1 = GenerationConfig(max_new_tokens=8, do_sample=True, temperature=1.2, seed=123)
    cfg_seed1_repeat = GenerationConfig(max_new_tokens=8, do_sample=True, temperature=1.2, seed=123)
    cfg_seed2 = GenerationConfig(max_new_tokens=8, do_sample=True, temperature=1.2, seed=999)

    res_1 = generator.generate(prompt, cfg_seed1)
    res_1_repeat = generator.generate(prompt, cfg_seed1_repeat)
    res_2 = generator.generate(prompt, cfg_seed2)

    # Same seed -> exact reproducibility
    assert res_1.generated_token_ids == res_1_repeat.generated_token_ids

    # Different seed -> distinct sampling sequence (over 8 tokens with high temperature)
    assert res_1.generated_token_ids != res_2.generated_token_ids


# ---------------------------------------------------------------------------
# 14. Generation Result Structure
# ---------------------------------------------------------------------------
def test_generation_result_structure(small_model: GPTModel, dummy_tokenizer: Tokenizer):
    generator = Generator(small_model, tokenizer=dummy_tokenizer, device="cpu")
    prompt = "hello test"
    cfg = GenerationConfig(max_new_tokens=4, do_sample=False)
    res = generator.generate(prompt, cfg)

    assert isinstance(res, GenerationResult)
    assert res.prompt == prompt
    assert isinstance(res.prompt_token_ids, list)
    assert isinstance(res.generated_token_ids, list)
    assert isinstance(res.text, str)
    assert res.prompt_tokens == len(res.prompt_token_ids)
    assert res.generated_tokens == len(res.generated_token_ids)
    assert res.total_tokens == res.prompt_tokens + res.generated_tokens
    assert res.generation_time > 0
    assert res.tokens_per_second > 0
    assert res.stopped_reason in {"max_tokens", "eos", "context_limit"}

    res_dict = res.to_dict()
    assert isinstance(res_dict, dict)
    assert "tokens_per_second" in res_dict


# ---------------------------------------------------------------------------
# 15. CPU Inference Verification & 16. No CUDA Usage
# ---------------------------------------------------------------------------
def test_cpu_device_and_no_cuda(small_model: GPTModel):
    generator = Generator(small_model, device="cpu")
    assert generator.device.type == "cpu"

    with pytest.raises(ValueError, match="Generator strictly requires CPU device"):
        Generator(small_model, device="cuda")

    # Verify execution leaves all tensors on CPU
    res = generator.generate([1, 2, 3], GenerationConfig(max_new_tokens=3))
    assert isinstance(res.generated_token_ids, list)
    for param in small_model.parameters():
        assert param.device.type == "cpu"


# ---------------------------------------------------------------------------
# 17. KV Cache Initialization, 18. Shape, 19. Growth, 20. Reset
# ---------------------------------------------------------------------------
def test_kv_cache_lifecycle(small_model: GPTModel):
    cache = KVCache(context_length=small_model.config.context_length)
    assert cache.is_empty
    assert cache.current_length == 0
    assert cache.get_shape() is None

    # Step 1: Prefill with 3 tokens
    input_ids = torch.tensor([[1, 2, 3]], dtype=torch.long)
    _, present_kvs = small_model(input_ids, past_key_values=None, use_cache=True)
    cache.update(present_kvs)

    assert not cache.is_empty
    assert cache.current_length == 3
    # Shape: [B, n_head, seq_len, head_dim]
    # head_dim = n_embd // n_head = 32 // 2 = 16
    expected_shape = (1, 2, 3, 16)
    assert cache.get_shape() == expected_shape

    # Step 2: Incremental step with 1 token
    next_input = torch.tensor([[4]], dtype=torch.long)
    _, present_kvs = small_model(next_input, past_key_values=cache.past_key_values, use_cache=True)
    cache.update(present_kvs)

    assert cache.current_length == 4
    assert cache.get_shape() == (1, 2, 4, 16)

    # Step 3: Reset
    cache.reset()
    assert cache.is_empty
    assert cache.current_length == 0
    assert cache.get_shape() is None


# ---------------------------------------------------------------------------
# 21. Full Forward vs Cached Forward Logit Equivalence
# ---------------------------------------------------------------------------
def test_full_forward_vs_cached_forward_equivalence(small_model: GPTModel):
    tokens = [4, 7, 12, 19]
    full_input = torch.tensor([tokens], dtype=torch.long)
    with torch.no_grad():
        full_logits = small_model(full_input, use_cache=False)

    cache = KVCache(context_length=small_model.config.context_length)
    with torch.no_grad():
        for i, tok in enumerate(tokens):
            step_input = torch.tensor([[tok]], dtype=torch.long)
            step_logits, present_kvs = small_model(
                step_input,
                past_key_values=cache.past_key_values,
                use_cache=True,
            )
            cache.update(present_kvs)
            # Logit comparison at position i
            max_diff = torch.max(torch.abs(step_logits[0, 0, :] - full_logits[0, i, :])).item()
            assert max_diff < 1e-4, f"Mismatch at position {i}: max difference {max_diff}"


# ---------------------------------------------------------------------------
# 22. Cached vs Naive Generation Token Equivalence
# ---------------------------------------------------------------------------
def test_cached_vs_naive_generation_equivalence(small_model: GPTModel):
    generator = Generator(small_model, device="cpu")
    prompt = [2, 5, 8, 11]
    cfg_naive = GenerationConfig(max_new_tokens=12, do_sample=False, use_cache=False)
    cfg_cached = GenerationConfig(max_new_tokens=12, do_sample=False, use_cache=True)

    res_naive = generator.generate(prompt, cfg_naive)
    res_cached = generator.generate(prompt, cfg_cached)

    assert res_naive.generated_token_ids == res_cached.generated_token_ids
    assert len(res_naive.generated_token_ids) == 12


# ---------------------------------------------------------------------------
# 23. Cache Context Overflow
# ---------------------------------------------------------------------------
def test_cache_context_overflow(small_model: GPTModel):
    # Context length is 32
    cache = KVCache(context_length=4)
    input_ids = torch.tensor([[1, 2, 3, 4, 5]], dtype=torch.long)
    _, present_kvs = small_model(input_ids, past_key_values=None, use_cache=True)

    with pytest.raises(ValueError, match="exceeds maximum context length"):
        cache.update(present_kvs)


# ---------------------------------------------------------------------------
# 24. Perplexity Calculation & 25. Token-Weighted Aggregation
# ---------------------------------------------------------------------------
def test_perplexity_and_token_weighted_aggregation(tmp_path: Path, small_model: GPTModel):
    assert calculate_perplexity(0.0) == 1.0
    assert math.isclose(calculate_perplexity(math.log(10.0)), 10.0, rel_tol=1e-5)
    assert calculate_perplexity(105.0) == float("inf")
    assert math.isnan(calculate_perplexity(float("nan")))

    # Synthetic binary dataset with 200 tokens
    tokens = list(range(1, 51)) * 4
    bin_path = tmp_path / "val_tokens.bin"
    np.array(tokens, dtype=np.uint32).tofile(bin_path)

    dataset = TokenDataset(bin_path, sequence_length=16, allow_cross_document_sequences=True)
    metrics = evaluate_perplexity(small_model, dataset, batch_size=2)

    assert metrics.num_batches > 0
    assert metrics.total_tokens > 0
    assert metrics.mean_loss > 0.0
    assert metrics.perplexity > 1.0
    assert metrics.tokens_per_sec > 0.0


# ---------------------------------------------------------------------------
# 26. Evaluation model.eval() & 27. torch.no_grad() Behavior
# ---------------------------------------------------------------------------
def test_evaluation_modes_and_state(tmp_path: Path, small_model: GPTModel):
    tokens = list(range(1, 51)) * 2
    bin_path = tmp_path / "val_modes.bin"
    np.array(tokens, dtype=np.uint32).tofile(bin_path)
    dataset = TokenDataset(bin_path, sequence_length=8, allow_cross_document_sequences=True)

    small_model.train(True)
    assert small_model.training is True

    metrics = evaluate_perplexity(small_model, dataset, batch_size=2, eval_batches=2)
    # Model training state must be restored after evaluation
    assert small_model.training is True

    # Check that parameters did not accumulate gradients
    for p in small_model.parameters():
        assert p.grad is None


# ---------------------------------------------------------------------------
# 28. Generation Evaluator Multi-Prompt
# ---------------------------------------------------------------------------
def test_generation_evaluator(small_model: GPTModel, dummy_tokenizer: Tokenizer):
    gen = Generator(small_model, tokenizer=dummy_tokenizer, device="cpu")
    evaluator = GenerationEvaluator(gen)
    prompts = ["hello", "world"]
    records = evaluator.evaluate_prompts(prompts, GenerationConfig(max_new_tokens=5, do_sample=False))

    assert len(records) == 2
    assert records[0].prompt == "hello"
    assert records[1].prompt == "world"
    assert records[0].token_count == 5

    table = evaluator.generate_summary_table(records)
    assert "| Prompt | Tokens |" in table
    assert "hello" in table


# ---------------------------------------------------------------------------
# 29. CLI Generation Smoke Test
# ---------------------------------------------------------------------------
def test_cli_generation_smoke(tmp_path: Path, small_model: GPTModel, dummy_tokenizer: Tokenizer):
    app_cfg = AppConfig()
    app_cfg.model = small_model.config
    opt = torch.optim.AdamW(small_model.parameters(), lr=1e-3)
    sched = CosineWarmupScheduler(
        opt,
        learning_rate=1e-3,
        min_learning_rate=1e-4,
        warmup_steps=5,
        max_steps=20,
    )
    state = TrainingState(global_step=1)
    tok_fp = compute_tokenizer_fingerprint(dummy_tokenizer)

    ckpt_path = save_checkpoint(
        checkpoint_dir=tmp_path,
        model=small_model,
        optimizer=opt,
        scheduler=sched,
        state=state,
        config=app_cfg,
        tokenizer_fingerprint=tok_fp,
    )
    tok_path = tmp_path / "tokenizer.json"
    dummy_tokenizer.save(tok_path)

    cmd = [
        sys.executable,
        "scripts/generate.py",
        "--checkpoint", str(ckpt_path),
        "--tokenizer", str(tok_path),
        "--prompt", "hello",
        "--max-new-tokens", "5",
        "--greedy",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    assert "Generating on CPU..." in res.stdout
    assert "prompt tokens:" in res.stdout
    assert "generated tokens: 5" in res.stdout


# ---------------------------------------------------------------------------
# 30. CLI Evaluation Smoke Test
# ---------------------------------------------------------------------------
def test_cli_evaluation_smoke(tmp_path: Path, small_model: GPTModel, dummy_tokenizer: Tokenizer):
    app_cfg = AppConfig()
    app_cfg.model = small_model.config
    opt = torch.optim.AdamW(small_model.parameters(), lr=1e-3)
    sched = CosineWarmupScheduler(
        opt,
        learning_rate=1e-3,
        min_learning_rate=1e-4,
        warmup_steps=5,
        max_steps=20,
    )
    state = TrainingState(global_step=1)
    tok_fp = compute_tokenizer_fingerprint(dummy_tokenizer)

    ckpt_path = save_checkpoint(
        checkpoint_dir=tmp_path,
        model=small_model,
        optimizer=opt,
        scheduler=sched,
        state=state,
        config=app_cfg,
        tokenizer_fingerprint=tok_fp,
    )
    tok_path = tmp_path / "tokenizer.json"
    dummy_tokenizer.save(tok_path)

    # Create dummy dataset
    tokens = list(range(1, 60))
    bin_path = tmp_path / "val_cli.bin"
    np.array(tokens, dtype=np.uint32).tofile(bin_path)

    cmd = [
        sys.executable,
        "scripts/evaluate.py",
        "--checkpoint", str(ckpt_path),
        "--tokenizer", str(tok_path),
        "--dataset", str(bin_path),
        "--batch-size", "2",
        "--eval-batches", "2",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    assert "MYLLM EVALUATION RESULTS (CPU)" in res.stdout
    assert "Perplexity:" in res.stdout


# ---------------------------------------------------------------------------
# 31. Benchmark Smoke Test & Speedup Check
# ---------------------------------------------------------------------------
def test_benchmark_smoke(small_model: GPTModel):
    res = benchmark_inference(
        model=small_model,
        prompt_ids=[1, 2, 3, 4],
        max_new_tokens=8,
        warmup_runs=1,
    )
    assert res.tokens_generated_naive == 8
    assert res.tokens_generated_cached == 8
    assert res.outputs_match is True
    assert res.cached_tokens_per_sec > 0
    assert res.naive_tokens_per_sec > 0
    assert res.speedup > 0


# ---------------------------------------------------------------------------
# 32. Non-Finite Logits & Numerical Stability
# ---------------------------------------------------------------------------
def test_sampling_safety_and_numerical_stability():
    cfg = GenerationConfig(do_sample=True)

    # 1. Non-finite logits raise InferenceError
    nan_logits = torch.tensor([1.0, float("nan"), 3.0])
    with pytest.raises(InferenceError, match="Encountered non-finite values"):
        sample_next_token(nan_logits, seen_tokens=[], config=cfg)

    inf_logits = torch.tensor([1.0, float("inf"), 3.0])
    with pytest.raises(InferenceError, match="Encountered non-finite values"):
        sample_next_token(inf_logits, seen_tokens=[], config=cfg)

    # 2. Large positive logits do not crash or produce NaNs
    large_logits = torch.tensor([1000.0, 1005.0, 990.0])
    tok = sample_next_token(large_logits, seen_tokens=[], config=cfg)
    assert tok in {0, 1, 2}

    # 3. Large negative logits do not crash
    neg_logits = torch.tensor([-1000.0, -995.0, -1010.0])
    tok_neg = sample_next_token(neg_logits, seen_tokens=[], config=cfg)
    assert tok_neg in {0, 1, 2}
