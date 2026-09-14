#!/usr/bin/env python3
"""
Performance Regression Guard and Benchmark Comparison Utility for MyLLM.

Compares a baseline benchmark JSON against a current benchmark JSON,
computes deltas and percentage changes, evaluates against regression thresholds,
and outputs human-readable console and markdown comparison tables.

Example:
    python scripts/compare_benchmarks.py \\
        --baseline benchmarks/phase11/baseline.json \\
        --current benchmarks/phase11/optimized.json \\
        --markdown benchmarks/phase11/comparison.md
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Tuple


def calc_change(before: float, after: float, higher_is_better: bool = False) -> Tuple[float, float, str]:
    """
    Calculate absolute delta, percentage change, and status indicator.
    
    Status:
        "IMPROVED" if faster (or higher throughput)
        "REGRESSED" if slower (or lower throughput)
        "UNCHANGED" if within 1% change
    """
    delta = after - before
    pct = (delta / before * 100.0) if before != 0 else 0.0

    if abs(pct) < 1.0:
        status = "UNCHANGED"
    elif higher_is_better:
        status = "IMPROVED" if delta > 0 else "REGRESSED"
    else:
        status = "IMPROVED" if delta < 0 else "REGRESSED"

    return delta, pct, status


def format_row(name: str, before: float, after: float, unit: str, higher_is_better: bool = False) -> Dict[str, Any]:
    delta, pct, status = calc_change(before, after, higher_is_better)
    sign = "+" if delta > 0 else ""
    return {
        "metric": name,
        "before": f"{before:.2f} {unit}",
        "after": f"{after:.2f} {unit}",
        "delta": f"{sign}{delta:.2f} {unit}",
        "percent_change": f"{sign}{pct:.1f}%",
        "status": status,
        "is_regression": (status == "REGRESSED"),
    }


def compare_benchmarks(
    baseline_data: Dict[str, Any],
    current_data: Dict[str, Any],
    threshold_pct: float = 10.0,
) -> Tuple[List[Dict[str, Any]], bool, str]:
    """
    Compare baseline against current metrics and generate a structured comparison table.
    
    Returns:
        (rows, has_critical_regression, markdown_content)
    """
    rows: List[Dict[str, Any]] = []

    # 1. Forward Pass Benchmarks
    b_fwd = {f"b{r['batch_size']}_s{r['sequence_length']}": r for r in baseline_data.get("forward_benchmarks", [])}
    c_fwd = {f"b{r['batch_size']}_s{r['sequence_length']}": r for r in current_data.get("forward_benchmarks", [])}
    for k in b_fwd:
        if k in c_fwd:
            rows.append(format_row(
                f"Forward Latency ({k})",
                b_fwd[k]["mean_latency_ms"],
                c_fwd[k]["mean_latency_ms"],
                "ms",
                higher_is_better=False,
            ))
            rows.append(format_row(
                f"Forward Throughput ({k})",
                b_fwd[k]["tokens_per_second"],
                c_fwd[k]["tokens_per_second"],
                "tok/s",
                higher_is_better=True,
            ))

    # 2. Inference & KV Cache
    b_kv = baseline_data.get("inference_kv_cache", {})
    c_kv = current_data.get("inference_kv_cache", {})
    if b_kv and c_kv:
        rows.append(format_row("Prompt Prefill Latency", b_kv["prefill_latency_ms"], c_kv["prefill_latency_ms"], "ms", False))
        rows.append(format_row("First Token Latency", b_kv["first_token_latency_ms"], c_kv["first_token_latency_ms"], "ms", False))
        rows.append(format_row("Naive Generation Throughput", b_kv["naive_tokens_per_sec"], c_kv["naive_tokens_per_sec"], "tok/s", True))
        rows.append(format_row("Cached Generation Throughput", b_kv["cached_tokens_per_sec"], c_kv["cached_tokens_per_sec"], "tok/s", True))
        rows.append(format_row("KV Cache Speedup", b_kv["kv_cache_speedup"], c_kv["kv_cache_speedup"], "x", True))

    # 3. Inference Modes
    b_im = baseline_data.get("inference_modes", {})
    c_im = current_data.get("inference_modes", {})
    if b_im and c_im:
        rows.append(format_row("torch.no_grad Throughput", b_im["no_grad"]["tokens_per_second"], c_im["no_grad"]["tokens_per_second"], "tok/s", True))
        rows.append(format_row("torch.inference_mode Throughput", b_im["inference_mode"]["tokens_per_second"], c_im["inference_mode"]["tokens_per_second"], "tok/s", True))

    # 4. Tokenizer
    b_tok = baseline_data.get("tokenizer", {})
    c_tok = current_data.get("tokenizer", {})
    for corpus in ["short_english", "medium_english", "long_english", "unicode_tamil"]:
        if corpus in b_tok and corpus in c_tok:
            rows.append(format_row(f"Tokenizer Encode ({corpus})", b_tok[corpus]["encode_tokens_per_sec"], c_tok[corpus]["encode_tokens_per_sec"], "tok/s", True))
            rows.append(format_row(f"Tokenizer Decode ({corpus})", b_tok[corpus]["decode_tokens_per_sec"], c_tok[corpus]["decode_tokens_per_sec"], "tok/s", True))

    # 5. Data Pipeline
    b_dp = baseline_data.get("data_pipeline", {})
    c_dp = current_data.get("data_pipeline", {})
    if b_dp and c_dp and "sequence_retrievals_per_sec" in b_dp and "sequence_retrievals_per_sec" in c_dp:
        rows.append(format_row("Memmap Open Latency", b_dp["memmap_open_latency_ms"], c_dp["memmap_open_latency_ms"], "ms", False))
        rows.append(format_row("Sequence Retrieval", b_dp["sequence_retrievals_per_sec"], c_dp["sequence_retrievals_per_sec"], "seq/s", True))
        rows.append(format_row("Batch Construction", b_dp["batches_per_sec"], c_dp["batches_per_sec"], "batches/s", True))

    # 6. Training Step
    b_tr = baseline_data.get("training_profile", {})
    c_tr = current_data.get("training_profile", {})
    if b_tr and c_tr and "mean_step_latency_ms" in b_tr and "mean_step_latency_ms" in c_tr:
        rows.append(format_row("Training Step Latency", b_tr["mean_step_latency_ms"], c_tr["mean_step_latency_ms"], "ms", False))
        rows.append(format_row("Training Throughput", b_tr["tokens_per_second"], c_tr["tokens_per_second"], "tok/s", True))

    # 7. API Endpoints
    b_api = baseline_data.get("api_benchmarks", {})
    c_api = current_data.get("api_benchmarks", {})
    if b_api and c_api:
        rows.append(format_row("API Health Latency", b_api["health_latency_ms"], c_api["health_latency_ms"], "ms", False))
        rows.append(format_row("API Chat Sync Latency", b_api["chat_sync_latency_ms"], c_api["chat_sync_latency_ms"], "ms", False))
        rows.append(format_row("API SSE First Token Latency", b_api["stream_first_token_latency_ms"], c_api["stream_first_token_latency_ms"], "ms", False))

    # 8. Memory RSS
    b_mem = baseline_data.get("memory_rss", {})
    c_mem = current_data.get("memory_rss", {})
    if b_mem and c_mem:
        rows.append(format_row("Process RSS (Model Loaded)", b_mem["rss_model_loaded_mb"], c_mem["rss_model_loaded_mb"], "MB", False))
        rows.append(format_row("Process RSS (API Idle)", b_mem["rss_api_idle_mb"], c_mem["rss_api_idle_mb"], "MB", False))
        rows.append(format_row("Process RSS (1 Session)", b_mem["rss_one_session_mb"], c_mem["rss_one_session_mb"], "MB", False))
        rows.append(format_row("Process RSS (5 Sessions)", b_mem["rss_five_sessions_mb"], c_mem["rss_five_sessions_mb"], "MB", False))

    # Determine if any critical regression exceeds threshold (focusing on raw latency, throughput, and memory)
    has_critical_regression = False
    for r in rows:
        if r["is_regression"] and "Speedup" not in r["metric"]:
            pct_val = abs(float(r["percent_change"].replace("%", "")))
            if pct_val > threshold_pct:
                has_critical_regression = True

    # Build Markdown Content
    md_lines = [
        "# Phase 11 CPU Performance Benchmark Comparison",
        "",
        f"- **Baseline Timestamp**: {baseline_data.get('timestamp', 'N/A')}",
        f"- **Current Timestamp**: {current_data.get('timestamp', 'N/A')}",
        f"- **PyTorch**: {current_data.get('environment', {}).get('pytorch_version', 'N/A')}",
        f"- **Processor**: {current_data.get('environment', {}).get('cpu_hardware', {}).get('processor', 'N/A')}",
        f"- **Regression Threshold**: {threshold_pct:.1f}%",
        "",
        "| Metric | Baseline | Current | Delta | % Change | Status |",
        "| :--- | :---: | :---: | :---: | :---: | :---: |",
    ]
    for r in rows:
        status_badge = f"**{r['status']}**" if r['status'] != "UNCHANGED" else "UNCHANGED"
        md_lines.append(
            f"| {r['metric']} | {r['before']} | {r['after']} | {r['delta']} | {r['percent_change']} | {status_badge} |"
        )
    md_lines.append("")

    return rows, has_critical_regression, "\n".join(md_lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare two MyLLM benchmark JSON reports.")
    parser.add_argument("--baseline", type=str, required=True, help="Path to baseline.json")
    parser.add_argument("--current", type=str, required=True, help="Path to current/optimized.json")
    parser.add_argument("--markdown", type=str, default=None, help="Optional path to output markdown report")
    parser.add_argument("--threshold", type=float, default=10.0, help="Regression threshold percentage (default: 10.0%%)")
    args = parser.parse_args()

    base_p = Path(args.baseline)
    curr_p = Path(args.current)

    if not base_p.is_file():
        print(f"Error: Baseline file not found: {base_p}", file=sys.stderr)
        return 1
    if not curr_p.is_file():
        print(f"Error: Current benchmark file not found: {curr_p}", file=sys.stderr)
        return 1

    with open(base_p, "r", encoding="utf-8") as f:
        baseline_data = json.load(f)
    with open(curr_p, "r", encoding="utf-8") as f:
        current_data = json.load(f)

    rows, has_regression, md_content = compare_benchmarks(
        baseline_data=baseline_data,
        current_data=current_data,
        threshold_pct=args.threshold,
    )

    print("=" * 80)
    print("           MyLLM Phase 11 Performance Comparison Report           ")
    print("=" * 80)
    print(f"{'Metric':<35} | {'Baseline':<12} | {'Current':<12} | {'Change':<10} | {'Status'}")
    print("-" * 80)
    for r in rows:
        print(f"{r['metric']:<35} | {r['before']:<12} | {r['after']:<12} | {r['percent_change']:<10} | {r['status']}")
    print("=" * 80)

    if args.markdown:
        md_p = Path(args.markdown)
        md_p.parent.mkdir(parents=True, exist_ok=True)
        md_p.write_text(md_content, encoding="utf-8")
        print(f"Markdown comparison written to: {md_p}")

    if has_regression:
        print(f"\n[WARNING] Critical performance regression detected exceeding {args.threshold}% threshold!")
        return 2

    print("\n[SUCCESS] Benchmark comparison complete. No critical regressions.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
