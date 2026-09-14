#!/usr/bin/env python3
"""
Comprehensive Phase 11 Performance Benchmark Suite for MyLLM.

Measures:
1. Environment and CPU hardware information
2. Model forward latency and throughput across batch sizes and sequence lengths
3. Forward pass component breakdown profiling
4. CPU threading analysis (1, 2, 4, 8 threads)
5. Inference latency (prefill, first-token, cached, naive, speedup, torch.inference_mode vs no_grad)
6. Tokenizer throughput and lossless round-trip across short, medium, long, and Tamil/Unicode texts
7. Data pipeline access and batch construction throughput
8. Training step latency breakdown (data, forward, backward, clip, optimizer, scheduler)
9. Local API endpoint latency and SSE streaming responsiveness
10. Process RSS memory across lifecycle states
11. Optional CPU compilation and mixed precision exploration

Outputs a standardized, machine-readable JSON report.
"""

from __future__ import annotations

import argparse
import asyncio
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import statistics
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import psutil
import torch
import torch.nn as nn
from torch.nn import functional as F

# Ensure repo root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from myllm.api.app import create_app
from myllm.config import AppConfig, ModelConfig, ServerConfig, TrainingConfig
from myllm.data.batching import BatchGenerator
from myllm.data.dataset import TokenDataset
from myllm.inference.cache import KVCache
from myllm.inference.generator import Generator
from myllm.inference.loader import load_inference_system
from myllm.inference.types import GenerationConfig
from myllm.model.gpt import GPTModel
from myllm.tokenizer import Tokenizer
from myllm.training.optimizer import create_optimizer
from myllm.training.scheduler import CosineWarmupScheduler
from myllm.utils.device import configure_cpu_threads, get_device_info, resolve_device
from myllm.utils.seed import set_seed


def get_environment_info() -> Dict[str, Any]:
    """Capture environment, CPU hardware, and thread settings."""
    cpu_info = {
        "processor": platform.processor() or "Unknown",
        "machine": platform.machine(),
        "physical_cores": psutil.cpu_count(logical=False),
        "logical_cores": psutil.cpu_count(logical=True),
        "total_memory_mb": round(psutil.virtual_memory().total / (1024 * 1024), 2),
    }
    dev_info = get_device_info(strict_cpu=True)
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "python_version": platform.python_version(),
        "python_compiler": platform.python_compiler(),
        "platform": platform.platform(),
        "pytorch_version": torch.__version__,
        "cpu_hardware": cpu_info,
        "default_intraop_threads": dev_info["num_cpu_threads"],
        "default_interop_threads": dev_info["num_interop_threads"],
        "cuda_available": dev_info["cuda_available_on_system"],
        "is_using_cuda": dev_info["is_using_cuda"],
    }


def benchmark_model_forward(
    model: GPTModel,
    device: torch.device,
    configs: List[Tuple[int, int]],
    warmup: int = 10,
    iterations: int = 30,
) -> List[Dict[str, Any]]:
    """Benchmark raw forward pass across batch sizes and sequence lengths."""
    results = []
    model.eval()

    with torch.no_grad():
        for batch_size, seq_len in configs:
            # Generate deterministic dummy inputs within vocab bounds
            input_ids = torch.randint(
                low=0,
                high=model.config.vocab_size,
                size=(batch_size, seq_len),
                dtype=torch.long,
                device=device,
            )

            # Warmup
            for _ in range(warmup):
                _ = model(input_ids)

            latencies = []
            for _ in range(iterations):
                t0 = time.perf_counter()
                _ = model(input_ids)
                latencies.append(time.perf_counter() - t0)

            mean_sec = statistics.mean(latencies)
            median_sec = statistics.median(latencies)
            total_tokens = batch_size * seq_len
            tokens_per_sec = total_tokens / mean_sec if mean_sec > 0 else 0.0

            results.append({
                "batch_size": batch_size,
                "sequence_length": seq_len,
                "total_tokens": total_tokens,
                "mean_latency_ms": round(mean_sec * 1000, 3),
                "median_latency_ms": round(median_sec * 1000, 3),
                "std_latency_ms": round(statistics.stdev(latencies) * 1000, 3) if len(latencies) > 1 else 0.0,
                "tokens_per_second": round(tokens_per_sec, 2),
            })

    return results


def profile_forward_components(
    model: GPTModel,
    device: torch.device,
    batch_size: int = 1,
    seq_len: int = 64,
    iterations: int = 15,
) -> Dict[str, Any]:
    """Measure granular time spent across model forward components."""
    model.eval()
    input_ids = torch.randint(
        low=0,
        high=model.config.vocab_size,
        size=(batch_size, seq_len),
        dtype=torch.long,
        device=device,
    )

    timings: Dict[str, List[float]] = {
        "embedding": [],
        "attention_qkv": [],
        "attention_scores": [],
        "attention_softmax": [],
        "attention_proj": [],
        "mlp": [],
        "layernorm": [],
        "lm_head": [],
    }

    # Warmup
    with torch.no_grad():
        for _ in range(5):
            _ = model(input_ids)

    # Detailed component timer
    with torch.no_grad():
        for _ in range(iterations):
            B, T = input_ids.size()
            pos = torch.arange(0, T, dtype=torch.long, device=device)

            # 1. Embedding
            t0 = time.perf_counter()
            tok_emb = model.transformer.wte(input_ids)
            pos_emb = model.transformer.wpe(pos)
            x = model.transformer.drop(tok_emb + pos_emb)
            timings["embedding"].append(time.perf_counter() - t0)

            # Blocks
            for block in model.transformer.h:
                # LN1
                t_ln1 = time.perf_counter()
                normed_x = block.ln_1(x)
                timings["layernorm"].append(time.perf_counter() - t_ln1)

                # Attention breakdown
                attn = block.attn
                t_qkv = time.perf_counter()
                qkv = attn.c_attn(normed_x)
                q, k, v = qkv.split(attn.n_embd, dim=2)
                q = q.view(B, T, attn.n_head, attn.head_dim).transpose(1, 2)
                k = k.view(B, T, attn.n_head, attn.head_dim).transpose(1, 2)
                v = v.view(B, T, attn.n_head, attn.head_dim).transpose(1, 2)
                timings["attention_qkv"].append(time.perf_counter() - t_qkv)

                t_scores = time.perf_counter()
                scale = 1.0 / (attn.head_dim ** 0.5)
                att = (q @ k.transpose(-2, -1)) * scale
                att = att.masked_fill(attn.causal_mask[:, :, :T, :T] == 0, float("-inf"))
                timings["attention_scores"].append(time.perf_counter() - t_scores)

                t_soft = time.perf_counter()
                att = F.softmax(att, dim=-1)
                att = attn.attn_dropout(att)
                y_val = att @ v
                timings["attention_softmax"].append(time.perf_counter() - t_soft)

                t_proj = time.perf_counter()
                y_val = y_val.transpose(1, 2).contiguous().view(B, T, attn.n_embd)
                y_val = attn.resid_dropout(attn.c_proj(y_val))
                timings["attention_proj"].append(time.perf_counter() - t_proj)

                x = x + y_val

                # LN2
                t_ln2 = time.perf_counter()
                normed_mlp = block.ln_2(x)
                timings["layernorm"].append(time.perf_counter() - t_ln2)

                # MLP
                t_mlp = time.perf_counter()
                mlp_out = block.mlp(normed_mlp)
                timings["mlp"].append(time.perf_counter() - t_mlp)
                x = x + mlp_out

            # Final LayerNorm
            t_lnf = time.perf_counter()
            x = model.transformer.ln_f(x)
            timings["layernorm"].append(time.perf_counter() - t_lnf)

            # LM Head
            t_lm = time.perf_counter()
            _ = model.lm_head(x)
            timings["lm_head"].append(time.perf_counter() - t_lm)

    summary = {}
    total_avg_sec = sum(statistics.mean(v) for v in timings.values())
    for comp, times in timings.items():
        avg_ms = statistics.mean(times) * 1000
        pct = (statistics.mean(times) / total_avg_sec * 100) if total_avg_sec > 0 else 0.0
        summary[comp] = {
            "mean_time_ms": round(avg_ms, 4),
            "percentage": round(pct, 2),
        }

    return {
        "batch_size": batch_size,
        "sequence_length": seq_len,
        "total_profiled_ms": round(total_avg_sec * 1000, 3),
        "components": summary,
    }


def benchmark_cpu_threading(
    model: GPTModel,
    device: torch.device,
    thread_counts: List[int],
    batch_size: int = 1,
    seq_len: int = 32,
    iterations: int = 10,
) -> List[Dict[str, Any]]:
    """Measure model forward latency across thread counts."""
    original_threads = torch.get_num_threads()
    results = []
    input_ids = torch.randint(
        low=0,
        high=model.config.vocab_size,
        size=(batch_size, seq_len),
        dtype=torch.long,
        device=device,
    )

    for num_t in thread_counts:
        try:
            torch.set_num_threads(num_t)
            # Warmup
            with torch.no_grad():
                for _ in range(3):
                    _ = model(input_ids)

            latencies = []
            with torch.no_grad():
                for _ in range(iterations):
                    t0 = time.perf_counter()
                    _ = model(input_ids)
                    latencies.append(time.perf_counter() - t0)

            mean_sec = statistics.mean(latencies)
            tok_sec = (batch_size * seq_len) / mean_sec if mean_sec > 0 else 0.0

            results.append({
                "threads": num_t,
                "mean_latency_ms": round(mean_sec * 1000, 3),
                "median_latency_ms": round(statistics.median(latencies) * 1000, 3),
                "tokens_per_second": round(tok_sec, 2),
            })
        finally:
            torch.set_num_threads(original_threads)

    return results


def benchmark_inference_modes(
    model: GPTModel,
    tokenizer: Tokenizer,
    prompt: str,
    max_new_tokens: int = 20,
    iterations: int = 5,
) -> Dict[str, Any]:
    """Compare torch.no_grad() vs torch.inference_mode() during autoregressive generation."""
    generator = Generator(model=model, tokenizer=tokenizer, device="cpu")
    cfg = GenerationConfig(max_new_tokens=max_new_tokens, do_sample=False, use_cache=True, stop_on_eos=False)

    # 1. Warmup
    _ = generator.generate(prompt, cfg)

    # 2. Benchmark under no_grad
    no_grad_latencies = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        with torch.no_grad():
            res_ng = generator.generate(prompt, cfg)
        no_grad_latencies.append(time.perf_counter() - t0)

    # 3. Benchmark under inference_mode
    inf_mode_latencies = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        with torch.inference_mode():
            res_im = generator.generate(prompt, cfg)
        inf_mode_latencies.append(time.perf_counter() - t0)

    # Equivalence check
    tokens_match = (res_ng.generated_token_ids == res_im.generated_token_ids)
    mean_ng_sec = statistics.mean(no_grad_latencies)
    mean_im_sec = statistics.mean(inf_mode_latencies)

    return {
        "prompt": prompt,
        "max_new_tokens": max_new_tokens,
        "tokens_match": tokens_match,
        "no_grad": {
            "mean_latency_ms": round(mean_ng_sec * 1000, 3),
            "tokens_per_second": round(max_new_tokens / mean_ng_sec, 2),
        },
        "inference_mode": {
            "mean_latency_ms": round(mean_im_sec * 1000, 3),
            "tokens_per_second": round(max_new_tokens / mean_im_sec, 2),
        },
        "speedup_ratio": round(mean_ng_sec / mean_im_sec, 3) if mean_im_sec > 0 else 1.0,
    }


def benchmark_inference_kv(
    model: GPTModel,
    tokenizer: Tokenizer,
    prompt: str,
    max_new_tokens: int = 20,
    iterations: int = 5,
) -> Dict[str, Any]:
    """Benchmark prompt prefill, first-token latency, cached vs naive generation."""
    generator = Generator(model=model, tokenizer=tokenizer, device="cpu")
    cfg_cached = GenerationConfig(max_new_tokens=max_new_tokens, do_sample=False, use_cache=True, stop_on_eos=False)
    cfg_naive = GenerationConfig(max_new_tokens=max_new_tokens, do_sample=False, use_cache=False, stop_on_eos=False)

    # Warmup
    _ = generator.generate(prompt, cfg_cached)
    _ = generator.generate(prompt, cfg_naive)

    prompt_ids = tokenizer.encode(prompt)

    # Measure prompt prefill latency
    prefill_latencies = []
    with torch.no_grad():
        in_tensor = torch.tensor([prompt_ids], dtype=torch.long, device="cpu")
        for _ in range(iterations):
            t0 = time.perf_counter()
            _ = model(in_tensor, use_cache=True)
            prefill_latencies.append(time.perf_counter() - t0)

    # Measure first-token latency (prefill + 1 token decode)
    cfg_single = GenerationConfig(max_new_tokens=1, do_sample=False, use_cache=True, stop_on_eos=False)
    first_token_latencies = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        _ = generator.generate(prompt, cfg_single)
        first_token_latencies.append(time.perf_counter() - t0)

    # Measure cached generation
    cached_latencies = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        res_cached = generator.generate(prompt, cfg_cached)
        cached_latencies.append(time.perf_counter() - t0)

    # Measure naive generation
    naive_latencies = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        res_naive = generator.generate(prompt, cfg_naive)
        naive_latencies.append(time.perf_counter() - t0)

    outputs_match = res_cached.generated_token_ids == res_naive.generated_token_ids
    mean_prefill_ms = statistics.mean(prefill_latencies) * 1000
    mean_first_token_ms = statistics.mean(first_token_latencies) * 1000
    mean_cached_sec = statistics.mean(cached_latencies)
    mean_naive_sec = statistics.mean(naive_latencies)

    cached_tps = max_new_tokens / mean_cached_sec if mean_cached_sec > 0 else 0.0
    naive_tps = max_new_tokens / mean_naive_sec if mean_naive_sec > 0 else 0.0
    speedup = cached_tps / naive_tps if naive_tps > 0 else 1.0

    return {
        "prompt": prompt,
        "prompt_tokens": len(prompt_ids),
        "new_tokens": max_new_tokens,
        "outputs_match": outputs_match,
        "prefill_latency_ms": round(mean_prefill_ms, 3),
        "first_token_latency_ms": round(mean_first_token_ms, 3),
        "naive_latency_ms": round(mean_naive_sec * 1000, 3),
        "naive_tokens_per_sec": round(naive_tps, 2),
        "cached_latency_ms": round(mean_cached_sec * 1000, 3),
        "cached_tokens_per_sec": round(cached_tps, 2),
        "kv_cache_speedup": round(speedup, 3),
    }


def benchmark_tokenizer(
    tokenizer: Tokenizer,
    iterations: int = 50,
) -> Dict[str, Any]:
    """Benchmark encode and decode throughput across various text corpora."""
    corpora = {
        "short_english": "Hello, world! Welcome to MyLLM.",
        "medium_english": (
            "MyLLM is an open-source Transformer built from scratch for pure CPU execution. "
            "It features custom Byte-Level BPE, causal self-attention, and KV cache."
        ),
        "long_english": (
            ("Artificial intelligence architectures have evolved rapidly over recent decades. "
             "Decoder-only language models utilize stacked attention mechanisms to forecast subsequent tokens. "
             "CPU execution requires careful memory management, zero-copy tensors, and optimized threading.\n") * 10
        ),
        "unicode_tamil": "வணக்கம் உலகம்! தமிழ் ஒரு தொன்மையான மொழி. 🚀🔥 Consumer CPU Transformer!",
    }

    results = {}
    for name, text in corpora.items():
        # Warmup
        _ = tokenizer.encode(text)
        sample_ids = tokenizer.encode(text)
        _ = tokenizer.decode(sample_ids)

        # Measure encode
        encode_times = []
        for _ in range(iterations):
            t0 = time.perf_counter()
            token_ids = tokenizer.encode(text)
            encode_times.append(time.perf_counter() - t0)

        # Measure decode
        decode_times = []
        for _ in range(iterations):
            t0 = time.perf_counter()
            _ = tokenizer.decode(token_ids)
            decode_times.append(time.perf_counter() - t0)

        mean_enc = statistics.mean(encode_times)
        mean_dec = statistics.mean(decode_times)
        char_count = len(text)
        token_count = len(token_ids)

        # Invariant verification
        round_trip_lossless = (tokenizer.decode(token_ids, skip_special_tokens=True) == text)

        results[name] = {
            "characters": char_count,
            "tokens": token_count,
            "round_trip_lossless": round_trip_lossless,
            "encode_latency_ms": round(mean_enc * 1000, 4),
            "encode_tokens_per_sec": round(token_count / mean_enc, 2) if mean_enc > 0 else 0.0,
            "decode_latency_ms": round(mean_dec * 1000, 4),
            "decode_tokens_per_sec": round(token_count / mean_dec, 2) if mean_dec > 0 else 0.0,
        }

    return results


def benchmark_data_pipeline(
    train_bin_path: Path,
    batch_size: int = 4,
    seq_len: int = 64,
    iterations: int = 50,
) -> Dict[str, Any]:
    """Benchmark memmap open, single sequence retrieval, and batch generator construction."""
    if not train_bin_path.is_file():
        return {"error": f"Dataset file not found: {train_bin_path}"}

    # 1. Memmap Open
    open_times = []
    for _ in range(10):
        t0 = time.perf_counter()
        ds = TokenDataset(train_bin_path, sequence_length=seq_len, allow_cross_document_sequences=True)
        open_times.append(time.perf_counter() - t0)
        ds.close()

    mean_open_ms = statistics.mean(open_times) * 1000

    # 2. Sequence retrieval from open dataset
    dataset = TokenDataset(train_bin_path, sequence_length=seq_len, allow_cross_document_sequences=True)
    num_samples = min(1000, len(dataset))
    # Warmup memory pages
    for i in range(min(200, num_samples)):
        _ = dataset[i]
    t0 = time.perf_counter()
    for i in range(num_samples):
        _ = dataset[i]
    retrieval_sec = time.perf_counter() - t0
    seqs_per_sec = num_samples / retrieval_sec if retrieval_sec > 0 else 0.0

    # 3. Batch construction
    batch_gen = BatchGenerator(dataset, batch_size=batch_size, shuffle=True, seed=42)
    batch_iter = iter(batch_gen)
    # Warmup batch iterator
    for _ in range(5):
        try:
            _ = next(batch_iter)
        except StopIteration:
            batch_iter = iter(batch_gen)
            _ = next(batch_iter)
    batch_times = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        try:
            _ = next(batch_iter)
        except StopIteration:
            batch_iter = iter(batch_gen)
            _ = next(batch_iter)
        batch_times.append(time.perf_counter() - t0)

    dataset.close()
    mean_batch_ms = statistics.mean(batch_times) * 1000
    batches_per_sec = 1000.0 / mean_batch_ms if mean_batch_ms > 0 else 0.0

    return {
        "dataset_total_tokens": dataset.total_tokens,
        "memmap_open_latency_ms": round(mean_open_ms, 4),
        "sequence_retrievals_per_sec": round(seqs_per_sec, 2),
        "batch_construction_latency_ms": round(mean_batch_ms, 4),
        "batches_per_sec": round(batches_per_sec, 2),
    }


def profile_training_step(
    model: GPTModel,
    train_bin_path: Path,
    batch_size: int = 4,
    seq_len: int = 64,
    steps: int = 10,
) -> Dict[str, Any]:
    """Profile CPU training step with granular component breakdown."""
    if not train_bin_path.is_file():
        return {"error": f"Training dataset not found: {train_bin_path}"}

    dataset = TokenDataset(train_bin_path, sequence_length=seq_len, allow_cross_document_sequences=True)
    batch_gen = BatchGenerator(dataset, batch_size=batch_size, shuffle=True, seed=42)
    batch_iter = iter(batch_gen)

    train_cfg = TrainingConfig(
        batch_size=batch_size,
        learning_rate=1e-3,
        weight_decay=0.01,
        max_steps=steps,
        warmup_steps=2,
    )
    optimizer = create_optimizer(model, train_cfg)
    scheduler = CosineWarmupScheduler(
        optimizer=optimizer,
        learning_rate=train_cfg.learning_rate,
        min_learning_rate=train_cfg.min_learning_rate,
        warmup_steps=train_cfg.warmup_steps,
        max_steps=train_cfg.max_steps,
    )
    model.train()

    timings = {
        "data_retrieval": [],
        "forward": [],
        "backward": [],
        "grad_clip": [],
        "optimizer": [],
        "scheduler": [],
    }
    step_latencies = []

    # Warmup steps (3 steps)
    for _ in range(3):
        inp, lbl = next(batch_iter)
        optimizer.zero_grad(set_to_none=True)
        _, l_w = model(inp, labels=lbl)
        l_w.backward()
        optimizer.step()
        scheduler.step(1)

    for step in range(steps):
        t_step_start = time.perf_counter()

        # 1. Data
        t0 = time.perf_counter()
        try:
            input_ids, labels = next(batch_iter)
        except StopIteration:
            batch_iter = iter(batch_gen)
            input_ids, labels = next(batch_iter)
        timings["data_retrieval"].append(time.perf_counter() - t0)

        # 2. Forward & Loss
        optimizer.zero_grad(set_to_none=True)
        t0 = time.perf_counter()
        _, loss = model(input_ids, labels=labels)
        timings["forward"].append(time.perf_counter() - t0)

        # 3. Backward
        t0 = time.perf_counter()
        loss.backward()
        timings["backward"].append(time.perf_counter() - t0)

        # 4. Grad Clip
        t0 = time.perf_counter()
        _ = torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        timings["grad_clip"].append(time.perf_counter() - t0)

        # 5. Optimizer
        t0 = time.perf_counter()
        optimizer.step()
        timings["optimizer"].append(time.perf_counter() - t0)

        # 6. Scheduler
        t0 = time.perf_counter()
        _ = scheduler.step(step + 1)
        timings["scheduler"].append(time.perf_counter() - t0)

        step_latencies.append(time.perf_counter() - t_step_start)

    dataset.close()
    mean_step_sec = statistics.mean(step_latencies)
    tokens_per_sec = (batch_size * seq_len) / mean_step_sec if mean_step_sec > 0 else 0.0

    breakdown = {}
    total_breakdown_sec = sum(statistics.mean(v) for v in timings.values())
    for comp, times in timings.items():
        avg_ms = statistics.mean(times) * 1000
        pct = (statistics.mean(times) / total_breakdown_sec * 100) if total_breakdown_sec > 0 else 0.0
        breakdown[comp] = {
            "mean_ms": round(avg_ms, 3),
            "percentage": round(pct, 2),
        }

    return {
        "steps_profiled": steps,
        "batch_size": batch_size,
        "sequence_length": seq_len,
        "mean_step_latency_ms": round(mean_step_sec * 1000, 3),
        "tokens_per_second": round(tokens_per_sec, 2),
        "breakdown": breakdown,
    }


def benchmark_api_endpoints(
    checkpoint_path: Path,
    tokenizer_path: Path,
) -> Dict[str, Any]:
    """Benchmark FastAPI server endpoints using TestClient."""
    from fastapi.testclient import TestClient

    server_cfg = ServerConfig(
        checkpoint=str(checkpoint_path),
        tokenizer=str(tokenizer_path),
        device="cpu",
        max_sessions=10,
    )
    app = create_app(config=server_cfg)

    with TestClient(app) as client:
        # Warmup routes to avoid measuring first-request framework compilation
        _ = client.get("/health")
        _ = client.get("/v1/model")
        w_sess = client.post("/v1/sessions", json={"system_prompt": "Warmup"})
        if w_sess.status_code in (200, 201):
            w_sid = w_sess.json()["session_id"]
            _ = client.post(f"/v1/sessions/{w_sid}/messages", json={"content": "Hi", "generation_config": {"max_new_tokens": 2}})
            with client.stream("POST", f"/v1/sessions/{w_sid}/messages/stream", json={"content": "Hi", "generation_config": {"max_new_tokens": 2}}) as s:
                for _ in s.iter_lines():
                    pass

        # 1. Health endpoint
        health_times = []
        for _ in range(10):
            t0 = time.perf_counter()
            resp = client.get("/health")
            health_times.append(time.perf_counter() - t0)
            assert resp.status_code == 200

        # 2. Model info endpoint
        model_info_times = []
        for _ in range(10):
            t0 = time.perf_counter()
            resp = client.get("/v1/model")
            model_info_times.append(time.perf_counter() - t0)
            assert resp.status_code == 200

        # 3. Session creation
        sess_times = []
        session_ids = []
        for _ in range(5):
            t0 = time.perf_counter()
            resp = client.post("/v1/sessions", json={"system_prompt": "You are a concise AI."})
            sess_times.append(time.perf_counter() - t0)
            assert resp.status_code in (200, 201)
            session_ids.append(resp.json()["session_id"])

        # 4. Synchronous chat generation
        sid = session_ids[0]
        chat_times = []
        for _ in range(3):
            t0 = time.perf_counter()
            resp = client.post(
                f"/v1/sessions/{sid}/messages",
                json={"content": "Hello!", "generation_config": {"max_new_tokens": 10}},
            )
            chat_times.append(time.perf_counter() - t0)
            assert resp.status_code == 200

        # 5. SSE streaming first token & completion
        sid2 = session_ids[1]
        stream_first_token_times = []
        stream_total_times = []

        for _ in range(3):
            t0 = time.perf_counter()
            first_tok_time = None
            with client.stream(
                "POST",
                f"/v1/sessions/{sid2}/messages/stream",
                json={"content": "Count 1 2 3", "generation_config": {"max_new_tokens": 10}},
            ) as stream_resp:
                for line in stream_resp.iter_lines():
                    if line.startswith("data:") and first_tok_time is None:
                        first_tok_time = time.perf_counter() - t0
            t_total = time.perf_counter() - t0
            if first_tok_time is not None:
                stream_first_token_times.append(first_tok_time)
            stream_total_times.append(t_total)

    return {
        "health_latency_ms": round(statistics.mean(health_times) * 1000, 3),
        "model_info_latency_ms": round(statistics.mean(model_info_times) * 1000, 3),
        "session_create_latency_ms": round(statistics.mean(sess_times) * 1000, 3),
        "chat_sync_latency_ms": round(statistics.mean(chat_times) * 1000, 3),
        "stream_first_token_latency_ms": round(statistics.mean(stream_first_token_times) * 1000, 3) if stream_first_token_times else 0.0,
        "stream_total_latency_ms": round(statistics.mean(stream_total_times) * 1000, 3),
    }


def measure_process_memory(
    checkpoint_path: Path,
    tokenizer_path: Path,
) -> Dict[str, Any]:
    """Measure resident set size (RSS) memory across model lifecycle states."""
    process = psutil.Process(os.getpid())

    # Baseline memory before model load
    rss_initial_mb = process.memory_info().rss / (1024 * 1024)

    # After model load
    model, tokenizer, _ = load_inference_system(checkpoint_path, tokenizer_path)
    rss_model_loaded_mb = process.memory_info().rss / (1024 * 1024)

    # API server initialized
    server_cfg = ServerConfig(
        checkpoint=str(checkpoint_path),
        tokenizer=str(tokenizer_path),
        device="cpu",
        max_sessions=20,
    )
    app = create_app(config=server_cfg)
    rss_api_idle_mb = process.memory_info().rss / (1024 * 1024)

    # Active sessions in API
    from fastapi.testclient import TestClient
    with TestClient(app) as client:
        # Create 1 session and send a message
        resp1 = client.post("/v1/sessions", json={"system_prompt": "Assistant"})
        sid1 = resp1.json()["session_id"]
        _ = client.post(f"/v1/sessions/{sid1}/messages", json={"content": "Hello"})
        rss_one_session_mb = process.memory_info().rss / (1024 * 1024)

        # Create 5 sessions and send messages
        for _ in range(4):
            r = client.post("/v1/sessions", json={"system_prompt": "Assistant"})
            s = r.json()["session_id"]
            _ = client.post(f"/v1/sessions/{s}/messages", json={"content": "Explain gravity"})
        rss_five_sessions_mb = process.memory_info().rss / (1024 * 1024)

    return {
        "rss_initial_mb": round(rss_initial_mb, 2),
        "rss_model_loaded_mb": round(rss_model_loaded_mb, 2),
        "rss_model_delta_mb": round(rss_model_loaded_mb - rss_initial_mb, 2),
        "rss_api_idle_mb": round(rss_api_idle_mb, 2),
        "rss_one_session_mb": round(rss_one_session_mb, 2),
        "rss_five_sessions_mb": round(rss_five_sessions_mb, 2),
    }


def investigate_optional_compilation_and_precision(
    model: GPTModel,
    device: torch.device,
    batch_size: int = 1,
    seq_len: int = 32,
    iterations: int = 10,
) -> Dict[str, Any]:
    """Investigate torch.compile and lower-precision autocast on CPU."""
    model.eval()
    input_ids = torch.randint(
        low=0,
        high=model.config.vocab_size,
        size=(batch_size, seq_len),
        dtype=torch.long,
        device=device,
    )

    # 1. Baseline FP32 Eager
    with torch.no_grad():
        for _ in range(3):
            _ = model(input_ids)
        latencies_fp32 = []
        for _ in range(iterations):
            t0 = time.perf_counter()
            _ = model(input_ids)
            latencies_fp32.append(time.perf_counter() - t0)
    mean_fp32_ms = statistics.mean(latencies_fp32) * 1000

    # 2. CPU Autocast (bfloat16)
    bf16_supported = True
    latencies_bf16 = []
    try:
        with torch.no_grad():
            with torch.autocast(device_type="cpu", dtype=torch.bfloat16):
                _ = model(input_ids)
                for _ in range(iterations):
                    t0 = time.perf_counter()
                    _ = model(input_ids)
                    latencies_bf16.append(time.perf_counter() - t0)
        mean_bf16_ms = statistics.mean(latencies_bf16) * 1000
    except Exception as e:
        bf16_supported = False
        mean_bf16_ms = 0.0

    # 3. Optional torch.compile on CPU
    compile_supported = True
    compile_first_run_sec = 0.0
    latencies_compile = []
    try:
        compiled_model = torch.compile(model)
        t0 = time.perf_counter()
        with torch.no_grad():
            _ = compiled_model(input_ids)
        compile_first_run_sec = time.perf_counter() - t0

        with torch.no_grad():
            for _ in range(iterations):
                t0 = time.perf_counter()
                _ = compiled_model(input_ids)
                latencies_compile.append(time.perf_counter() - t0)
        mean_compiled_ms = statistics.mean(latencies_compile) * 1000
    except Exception as e:
        compile_supported = False
        mean_compiled_ms = 0.0

    return {
        "eager_fp32_latency_ms": round(mean_fp32_ms, 3),
        "bf16_autocast_supported": bf16_supported,
        "bf16_autocast_latency_ms": round(mean_bf16_ms, 3) if bf16_supported else None,
        "bf16_speedup_vs_fp32": round(mean_fp32_ms / mean_bf16_ms, 3) if (bf16_supported and mean_bf16_ms > 0) else None,
        "torch_compile_supported": compile_supported,
        "torch_compile_first_run_overhead_sec": round(compile_first_run_sec, 3) if compile_supported else None,
        "torch_compile_steady_state_latency_ms": round(mean_compiled_ms, 3) if compile_supported else None,
        "torch_compile_speedup_vs_eager": round(mean_fp32_ms / mean_compiled_ms, 3) if (compile_supported and mean_compiled_ms > 0) else None,
    }


def run_full_benchmark(
    checkpoint_path: Path,
    tokenizer_path: Path,
    train_bin_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Execute the end-to-end benchmark suite and produce a standardized dictionary."""
    set_seed(42)
    device = resolve_device("cpu", strict_cpu=True)

    print("=" * 70)
    print("  MyLLM Phase 11 Full CPU Performance Benchmark Suite")
    print("=" * 70)

    # 1. Environment
    print("[1/11] Collecting CPU environment and hardware specifications...")
    env_info = get_environment_info()

    # 2. Model & Tokenizer Load
    print(f"[2/11] Loading model checkpoint: {checkpoint_path}")
    model, tokenizer, metadata = load_inference_system(checkpoint_path, tokenizer_path)
    param_count = sum(p.numel() for p in model.parameters())
    tied_weights = (model.transformer.wte.weight is model.lm_head.weight)

    model_info = {
        "checkpoint": str(checkpoint_path),
        "tokenizer": str(tokenizer_path),
        "parameter_count": param_count,
        "context_length": model.config.context_length,
        "vocab_size": model.config.vocab_size,
        "n_layer": model.config.n_layer,
        "n_head": model.config.n_head,
        "n_embd": model.config.n_embd,
        "tied_weights": tied_weights,
    }

    # 3. Forward Pass Across Shapes
    print("[3/11] Benchmarking raw model forward pass across batch/sequence configurations...")
    forward_shapes = [(1, 16), (1, 64), (4, 16), (4, 64)]
    forward_results = benchmark_model_forward(model, device, forward_shapes)

    # 4. Forward Component Profiling
    print("[4/11] Profiling forward pass component breakdown...")
    profile_results = profile_forward_components(model, device, batch_size=1, seq_len=64)

    # 5. CPU Threading
    print("[5/11] Analyzing CPU thread scaling (1, 2, 4, 8 threads)...")
    threading_results = benchmark_cpu_threading(model, device, [1, 2, 4, 8], batch_size=1, seq_len=32)

    # 6. Inference Modes (no_grad vs inference_mode)
    print("[6/11] Evaluating inference modes (torch.no_grad vs torch.inference_mode)...")
    test_prompt = "The future of artificial intelligence on consumer CPUs is"
    inference_modes_res = benchmark_inference_modes(model, tokenizer, test_prompt, max_new_tokens=20)

    # 7. KV Cache vs Naive Inference
    print("[7/11] Benchmarking autoregressive inference and KV cache speedup...")
    kv_cache_res = benchmark_inference_kv(model, tokenizer, test_prompt, max_new_tokens=20)

    # 8. Tokenizer
    print("[8/11] Benchmarking Byte-Level BPE tokenizer across text corpora...")
    tokenizer_res = benchmark_tokenizer(tokenizer)

    # 9. Data Pipeline
    print("[9/11] Benchmarking data pipeline and memory-mapped retrieval...")
    if train_bin_path is None:
        train_bin_path = REPO_ROOT / "data" / "tokenized" / "train.bin"
    data_pipeline_res = benchmark_data_pipeline(train_bin_path)

    # 10. Training Step Breakdown
    print("[10/11] Profiling CPU training step and gradient overhead...")
    training_res = profile_training_step(model, train_bin_path, batch_size=4, seq_len=64, steps=10)

    # 11. API, Memory & Compilation Exploration
    print("[11/11] Benchmarking local API, RSS memory footprint, and compilation options...")
    api_res = benchmark_api_endpoints(checkpoint_path, tokenizer_path)
    memory_res = measure_process_memory(checkpoint_path, tokenizer_path)
    compile_res = investigate_optional_compilation_and_precision(model, device)

    full_report: Dict[str, Any] = {
        "suite_version": "1.0",
        "timestamp": env_info["timestamp"],
        "environment": env_info,
        "model": model_info,
        "forward_benchmarks": forward_results,
        "forward_component_profile": profile_results,
        "cpu_threading": threading_results,
        "inference_modes": inference_modes_res,
        "inference_kv_cache": kv_cache_res,
        "tokenizer": tokenizer_res,
        "data_pipeline": data_pipeline_res,
        "training_profile": training_res,
        "api_benchmarks": api_res,
        "memory_rss": memory_res,
        "compilation_and_precision": compile_res,
    }

    if output_path is not None:
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        with open(out_p, "w", encoding="utf-8") as f:
            json.dump(full_report, f, indent=2)
        print(f"\nSaved benchmark report to: {out_p}")

    print("=" * 70)
    print("  Benchmark Suite Completed Successfully.")
    print("=" * 70)
    return full_report


def main() -> None:
    parser = argparse.ArgumentParser(description="MyLLM Phase 11 Full CPU Performance Benchmark Suite")
    parser.add_argument(
        "--checkpoint",
        type=str,
        default="experiments/phase7/phase7_sft_run/checkpoints/best.pt",
        help="Path to trained checkpoint",
    )
    parser.add_argument(
        "--tokenizer",
        type=str,
        default="data/tokenized/tokenizer.json",
        help="Path to tokenizer",
    )
    parser.add_argument(
        "--train-dataset",
        type=str,
        default="data/tokenized/train.bin",
        help="Path to training dataset",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="benchmarks/phase11/baseline.json",
        help="Path to save JSON benchmark output",
    )
    args = parser.parse_args()

    run_full_benchmark(
        checkpoint_path=Path(args.checkpoint),
        tokenizer_path=Path(args.tokenizer),
        train_bin_path=Path(args.train_dataset),
        output_path=Path(args.output),
    )


if __name__ == "__main__":
    main()
