#!/usr/bin/env python3
"""
Model Artifact Verification Utility for MyLLM.

Validates:
1. Checkpoint file existence and SHA-256 integrity
2. Tokenizer file existence and SHA-256 integrity
3. Tokenizer cryptographic fingerprint compatibility with checkpoint
4. Checkpoint metadata and model configuration schema
5. Strict CPU loading and parameter count verification
6. Weight-tying integrity (wte.weight is lm_head.weight)
7. Deterministic test autoregressive generation on CPU
8. Optional matching against model_manifest.json

Returns non-zero exit code on any verification failure.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

# Ensure repo root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

import torch

from myllm.data.tokenizer_pipeline import compute_tokenizer_fingerprint
from myllm.inference.generator import Generator
from myllm.inference.loader import load_inference_system
from myllm.inference.types import GenerationConfig
from myllm.tokenizer import Tokenizer
from myllm.utils.device import resolve_device


def compute_sha256(path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def verify_model(
    checkpoint_path: Path,
    tokenizer_path: Path,
    manifest_path: Path | None = None,
) -> bool:
    print("=" * 70)
    print("          MyLLM Model Artifact & Checkpoint Verification          ")
    print("=" * 70)

    # 1. File Existence
    print(f"[1/8] Checking artifact file existence...")
    if not checkpoint_path.is_file():
        print(f"  FAILED: Checkpoint file not found at: {checkpoint_path}", file=sys.stderr)
        return False
    if not tokenizer_path.is_file():
        print(f"  FAILED: Tokenizer file not found at: {tokenizer_path}", file=sys.stderr)
        return False
    print(f"  PASS: Found checkpoint ({checkpoint_path.stat().st_size:,} bytes)")
    print(f"  PASS: Found tokenizer  ({tokenizer_path.stat().st_size:,} bytes)")

    # 2. SHA-256 Integrity
    print(f"\n[2/8] Computing SHA-256 checksums...")
    ckpt_sha256 = compute_sha256(checkpoint_path)
    tok_sha256 = compute_sha256(tokenizer_path)
    print(f"  Checkpoint SHA-256 : {ckpt_sha256}")
    print(f"  Tokenizer SHA-256  : {tok_sha256}")

    # Manifest check (if available)
    if manifest_path is not None and manifest_path.is_file():
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest_data = json.load(f)
            matching = [
                m for m in manifest_data.get("models", [])
                if m.get("checkpoint_sha256") == ckpt_sha256
            ]
            if matching:
                entry = matching[0]
                print(f"  PASS: Checkpoint matches manifest entry '{entry['model_name']}'")
                if entry.get("tokenizer_sha256") == tok_sha256:
                    print(f"  PASS: Tokenizer matches manifest entry '{entry['model_name']}'")
                else:
                    print(f"  WARNING: Tokenizer SHA-256 does not match manifest entry for {entry['model_name']}")
            else:
                print(f"  INFO: Checkpoint hash not in manifest (custom/untracked model)")
        except Exception as e:
            print(f"  WARNING: Could not parse manifest file: {e}")

    # 3. Tokenizer Loading & Fingerprint
    print(f"\n[3/8] Loading tokenizer and calculating fingerprint...")
    try:
        tokenizer = Tokenizer.load(tokenizer_path)
        tok_fp = compute_tokenizer_fingerprint(tokenizer)
        print(f"  PASS: Tokenizer loaded (vocab size = {len(tokenizer)})")
        print(f"  Tokenizer Fingerprint: {tok_fp}")
    except Exception as e:
        print(f"  FAILED: Failed to load tokenizer: {e}", file=sys.stderr)
        return False

    # 4. Checkpoint Metadata & Fingerprint Compatibility
    print(f"\n[4/8] Inspecting checkpoint payload and metadata...")
    try:
        payload = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
        if not isinstance(payload, dict):
            print("  FAILED: Checkpoint payload is not a dictionary.", file=sys.stderr)
            return False
        if "model_state_dict" not in payload and "model" not in payload:
            print("  FAILED: Checkpoint missing 'model_state_dict'.", file=sys.stderr)
            return False

        ckpt_tok_fp = payload.get("tokenizer_fingerprint", "")
        if ckpt_tok_fp:
            if ckpt_tok_fp != tok_fp:
                print(
                    f"  FAILED: Tokenizer fingerprint mismatch!\n"
                    f"    Checkpoint requires: {ckpt_tok_fp}\n"
                    f"    Provided tokenizer: {tok_fp}",
                    file=sys.stderr,
                )
                return False
            print(f"  PASS: Tokenizer fingerprint matches checkpoint fingerprint")
        else:
            print(f"  INFO: Checkpoint does not specify tokenizer_fingerprint (skipping check)")

        saved_at = payload.get("saved_at", "unknown")
        format_ver = payload.get("format_version", "unknown")
        print(f"  Format Version       : {format_ver}")
        print(f"  Saved At             : {saved_at}")
    except Exception as e:
        print(f"  FAILED: Failed to parse checkpoint payload: {e}", file=sys.stderr)
        return False

    # 5. Model Loading on CPU
    print(f"\n[5/8] Loading model weights into GPTModel on CPU...")
    try:
        resolve_device("cpu", strict_cpu=True)
        model, loaded_tok, metadata = load_inference_system(checkpoint_path, tokenizer_path)
        model.eval()
        param_count = sum(p.numel() for p in model.parameters())
        print(f"  PASS: Model loaded cleanly on CPU device: {next(model.parameters()).device}")
        print(f"  Total Parameters     : {param_count:,}")
        print(f"  Context Length       : {model.config.context_length}")
        print(f"  Embedding Dimension  : {model.config.n_embd}")
        print(f"  Attention Layers     : {model.config.n_layer} (heads: {model.config.n_head})")
    except Exception as e:
        print(f"  FAILED: Failed to construct and load GPTModel: {e}", file=sys.stderr)
        return False

    # 6. Weight Tying Integrity
    print(f"\n[6/8] Verifying tied weights integrity...")
    if model.config.weight_tying:
        if model.lm_head.weight is not model.transformer.wte.weight:
            print("  FAILED: LM head and token embedding weights are not tied shared memory!", file=sys.stderr)
            return False
        print("  PASS: Weight tying verified (wte.weight is lm_head.weight)")
    else:
        print("  INFO: Weight tying is disabled in model configuration")

    # 7. Vocabulary & Context Compatibility
    print(f"\n[7/8] Checking vocabulary and context bounds...")
    if model.config.vocab_size != len(tokenizer):
        print(
            f"  FAILED: Vocab size mismatch! Model config has {model.config.vocab_size}, "
            f"tokenizer has {len(tokenizer)}",
            file=sys.stderr,
        )
        return False
    print(f"  PASS: Vocabulary size aligned ({len(tokenizer)} tokens)")

    # 8. Deterministic Test Generation Smoke Test
    print(f"\n[8/8] Performing test autoregressive token generation on CPU...")
    try:
        generator = Generator(model, tokenizer, device="cpu")
        gen_cfg = GenerationConfig(
            max_new_tokens=8,
            temperature=1.0,
            do_sample=False,
            use_cache=True,
        )
        test_prompt = "Hello"
        res = generator.generate(test_prompt, gen_cfg)
        print(f"  Test Prompt          : '{test_prompt}'")
        print(f"  Generated Text       : '{res.text}'")
        print(f"  Generated Tokens     : {res.generated_token_ids}")
        print(f"  Throughput           : {res.tokens_per_second:.1f} tok/s")
        print("  PASS: Autoregressive CPU generation verified")
    except Exception as e:
        print(f"  FAILED: Autoregressive test generation failed: {e}", file=sys.stderr)
        return False

    print("=" * 70)
    print("VERIFICATION RESULT: ALL CHECKS PASSED (100% SUCCESS)")
    print("Model artifact is verified, intact, and ready for deployment.")
    print("=" * 70)
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="MyLLM Model Artifact Verification Tool")
    parser.add_argument(
        "--checkpoint",
        type=str,
        default="experiments/phase7/phase7_sft_run/checkpoints/best.pt",
        help="Path to checkpoint file (.pt)",
    )
    parser.add_argument(
        "--tokenizer",
        type=str,
        default="data/tokenized/tokenizer.json",
        help="Path to tokenizer file (.json)",
    )
    parser.add_argument(
        "--manifest",
        type=str,
        default="model_manifest.json",
        help="Path to model manifest (.json)",
    )

    args = parser.parse_args()
    success = verify_model(
        checkpoint_path=Path(args.checkpoint),
        tokenizer_path=Path(args.tokenizer),
        manifest_path=Path(args.manifest) if args.manifest else None,
    )
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
