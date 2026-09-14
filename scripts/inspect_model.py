#!/usr/bin/env python3
"""
Model inspection script for MyLLM.

Constructs the GPT-style Transformer model using project configuration,
prints architectural and parameter statistics, runs a CPU forward pass,
measures latency, and verifies that logits are finite.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Ensure src is in python path
repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root / "src"))

import torch
from myllm.config import load_config
from myllm.model import GPTModel, count_parameters, get_model_summary
from myllm.tokenizer import Tokenizer
from myllm.utils.device import resolve_device, configure_cpu_threads


def main() -> int:
    print("=" * 65)
    print("            MyLLM Transformer Model Architecture Inspection        ")
    print("=" * 65)

    # 1. Load project configuration
    app_config = load_config()
    model_config = app_config.model

    # 2. Resolve CPU device and threads
    device = resolve_device(app_config.system.device, strict_cpu=app_config.system.strict_cpu)
    if app_config.system.num_threads:
        configure_cpu_threads(app_config.system.num_threads)

    # 3. Determine vocab_size (from existing tokenizer file or model_config)
    tok_path = Path("checkpoints/tokenizer.json")
    if tok_path.is_file():
        tokenizer = Tokenizer.load(tok_path)
        vocab_size = len(tokenizer)
        print(f"Loaded tokenizer from {tok_path} (vocab_size={vocab_size})")
    else:
        # Demo corpus tokenizer for inspection
        demo_corpus = ["Hello world from MyLLM pure CPU transformer."]
        tokenizer = Tokenizer.train(demo_corpus, vocab_size=300)
        vocab_size = len(tokenizer)
        print(f"Created demo tokenizer (vocab_size={vocab_size})")

    model_config.vocab_size = vocab_size

    # 4. Build GPT model
    model = GPTModel(model_config).to(device)
    model.eval()

    # 5. Print Architecture Summary & Parameters
    summary = get_model_summary(model)
    print(summary)

    counts = count_parameters(model)

    # 6. Create sample input on CPU
    sample_text = "Hello world from MyLLM"
    input_ids = tokenizer.encode(sample_text)
    input_tensor = torch.tensor([input_ids], dtype=torch.long, device=device)
    B, T = input_tensor.shape

    # 7. Run forward pass and measure elapsed time
    start_time = time.perf_counter()
    with torch.no_grad():
        logits = model(input_tensor)
    elapsed_time = time.perf_counter() - start_time

    # 8. Diagnostics and verification
    is_finite = bool(torch.isfinite(logits).all().item())
    has_nans = bool(torch.isnan(logits).any().item())
    has_infs = bool(torch.isinf(logits).any().item())

    print("\n--- Forward Pass Verification ---")
    print(f"Sample Input Text        : {sample_text!r}")
    print(f"Input Tensor Shape [B, T]: {list(input_tensor.shape)}")
    print(f"Output Logits Shape      : {list(logits.shape)}")
    print(f"Compute Device           : {logits.device} (type: {logits.device.type})")
    print(f"Forward Pass Duration    : {elapsed_time * 1000:.3f} ms")
    print(f"Logits are Finite        : {is_finite}")
    print(f"Logits Contain NaNs      : {has_nans}")
    print(f"Logits Contain Infs      : {has_infs}")
    print("=" * 65)

    if not is_finite or has_nans or has_infs:
        print("ERROR: Non-finite values detected in logits!", file=sys.stderr)
        return 1

    if logits.device.type != "cpu":
        print(f"ERROR: Model executed on non-CPU device {logits.device}!", file=sys.stderr)
        return 1

    print("SUCCESS: Model architecture verified. Pure CPU forward pass confirmed.")
    print("=" * 65)
    return 0


if __name__ == "__main__":
    sys.exit(main())
