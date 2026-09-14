"""
Experiment Tracking, JSONL Metrics Telemetry, and Training Report Generation.

Maintains a self-contained experiment directory containing:
- config.yaml: Snapshot of application configuration.
- metrics.jsonl: Line-by-line machine-readable telemetry.
- summary.json: Final metrics, timings, and best-checkpoint indicators.
- training_report.md: Human-readable markdown report with loss trajectories and overfitting diagnostics.
- generations_before.txt / generations_after.txt: Prompt completion quality evaluations.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml
from myllm.config import AppConfig
from myllm.training.state import TrainingState

logger = logging.getLogger(__name__)


class ExperimentTracker:
    """
    Coordinates experiment artifacts, telemetry streaming, and report generation.
    """

    def __init__(
        self,
        experiment_dir: Path | str,
        config: AppConfig,
        experiment_name: Optional[str] = None,
    ) -> None:
        if experiment_name:
            self.root_dir = Path(experiment_dir) / experiment_name
        else:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            self.root_dir = Path(experiment_dir) / f"run_{timestamp}"

        self.root_dir.mkdir(parents=True, exist_ok=True)
        self.config = config

        self.metrics_jsonl_path = self.root_dir / "metrics.jsonl"
        self.summary_json_path = self.root_dir / "summary.json"
        self.report_md_path = self.root_dir / "training_report.md"
        self.config_yaml_path = self.root_dir / "config.yaml"

        # Checkpoints directory inside experiment folder
        self.checkpoint_dir = self.root_dir / "checkpoints"
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

        # Update paths config to point to experiment checkpoints
        self.config.paths.checkpoint_dir = str(self.checkpoint_dir)

        # Save snapshot of config.yaml
        with open(self.config_yaml_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(self.config.to_dict(), f, sort_keys=False)

        self.metric_history: List[Dict[str, Any]] = []
        self.start_time = datetime.now(timezone.utc)
        self.initial_val_loss: Optional[float] = None
        self.final_val_loss: Optional[float] = None

    def log_step_metrics(self, state: TrainingState, is_val: bool = False, is_best: bool = False) -> None:
        """Stream a training or validation step record to metrics.jsonl."""
        record: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "global_step": state.global_step,
            "epoch": state.epoch,
            "train_loss": state.train_loss,
            "learning_rate": state.current_lr,
            "grad_norm": state.grad_norm,
            "tokens_seen": state.tokens_seen,
            "samples_seen": state.samples_seen,
            "elapsed_seconds": state.elapsed_seconds,
            "is_val_step": is_val,
            "is_best": is_best,
        }
        if is_val:
            record["val_loss"] = state.val_loss
            record["best_val_loss"] = state.best_val_loss
            record["best_val_perplexity"] = state.best_val_perplexity
            if self.initial_val_loss is None and state.val_loss == state.val_loss:  # not NaN
                self.initial_val_loss = state.val_loss
            self.final_val_loss = state.val_loss

        self.metric_history.append(record)

        # Append to JSONL file
        with open(self.metrics_jsonl_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

    def save_generation_samples(self, samples: List[Dict[str, str]], stage: str = "before") -> Path:
        """
        Save prompt generation samples to generations_before.txt or generations_after.txt.
        """
        filename = f"generations_{stage}.txt"
        target_path = self.root_dir / filename
        lines = [
            f"=== GENERATION EVALUATION ({stage.upper()} TRAINING) ===",
            f"Timestamp: {datetime.now(timezone.utc).isoformat()}",
            "=" * 60,
        ]
        for i, s in enumerate(samples, 1):
            lines.append(f"\n[Prompt {i}]:")
            lines.append(s.get("prompt", ""))
            lines.append(f"\n[Generated {i}]:")
            lines.append(s.get("text", ""))
            lines.append("-" * 40)

        with open(target_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        return target_path

    def diagnose_overfitting(self, final_state: TrainingState) -> Dict[str, Any]:
        """Analyze metric history for overfitting, underfitting, or divergence."""
        diagnostics = {
            "status": "healthy",
            "warnings": [],
            "loss_ratio": None,
        }

        # Check train loss progression
        train_losses = [m["train_loss"] for m in self.metric_history if m.get("train_loss") is not None and m["train_loss"] == m["train_loss"]]
        if len(train_losses) >= 2:
            first_train = train_losses[0]
            last_train = train_losses[-1]
            if last_train >= first_train:
                diagnostics["warnings"].append(
                    f"Underfitting detected: Train loss failed to decrease ({first_train:.4f} -> {last_train:.4f})."
                )
                diagnostics["status"] = "warning"

        # Check validation divergence (overfitting)
        if final_state.val_loss == final_state.val_loss and final_state.train_loss == final_state.train_loss and final_state.train_loss > 0:
            ratio = final_state.val_loss / final_state.train_loss
            diagnostics["loss_ratio"] = ratio
            if ratio > 2.0:
                diagnostics["warnings"].append(
                    f"Possible overfitting: Validation loss ({final_state.val_loss:.4f}) is "
                    f"{ratio:.2f}x higher than training loss ({final_state.train_loss:.4f})."
                )
                diagnostics["status"] = "warning"

        return diagnostics

    def finalize_experiment(self, final_state: TrainingState, total_elapsed_sec: float) -> Path:
        """Write summary.json and generate the complete training_report.md."""
        end_time = datetime.now(timezone.utc)
        diagnostics = self.diagnose_overfitting(final_state)

        # 1. summary.json
        summary = {
            "experiment_name": self.root_dir.name,
            "started_at": self.start_time.isoformat(),
            "ended_at": end_time.isoformat(),
            "total_elapsed_seconds": total_elapsed_sec,
            "final_step": final_state.global_step,
            "total_tokens_seen": final_state.tokens_seen,
            "total_samples_seen": final_state.samples_seen,
            "final_train_loss": final_state.train_loss,
            "final_val_loss": final_state.val_loss,
            "best_val_loss": final_state.best_val_loss,
            "best_val_perplexity": final_state.best_val_perplexity,
            "initial_val_loss": self.initial_val_loss,
            "average_throughput_tok_sec": final_state.tokens_seen / max(1e-6, total_elapsed_sec),
            "diagnostics": diagnostics,
            "config": self.config.to_dict(),
        }

        with open(self.summary_json_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        # 2. training_report.md
        report_lines = [
            f"# Training Experiment Report: `{self.root_dir.name}`",
            "",
            "## 1. Executive Summary",
            "",
            f"- **Execution Device**: Pure CPU (`{self.config.system.device}`, threads: {self.config.system.num_threads})",
            f"- **Duration**: {total_elapsed_sec:.2f} seconds ({summary['average_throughput_tok_sec']:,.0f} tokens/s)",
            f"- **Completed Steps**: {final_state.global_step:,} / {self.config.training.max_steps:,}",
            f"- **Tokens Processed**: {final_state.tokens_seen:,}",
            f"- **Final Train Loss**: {final_state.train_loss:.4f}",
            f"- **Best Val Loss**: {final_state.best_val_loss:.4f} (Perplexity: {final_state.best_val_perplexity:.2f})",
            f"- **Final Val Loss**: {final_state.val_loss:.4f}",
            "",
            "## 2. Checkpoints Status",
            "",
            f"- **Best Checkpoint**: `{self.checkpoint_dir / 'best.pt'}` (Validation Loss: {final_state.best_val_loss:.4f})",
            f"- **Final Checkpoint**: `{self.checkpoint_dir / 'latest.pt'}` (Global Step: {final_state.global_step})",
            "",
            "## 3. Overfitting / Underfitting Diagnostics",
            "",
            f"- **Status**: `{diagnostics['status'].upper()}`",
        ]
        if diagnostics["loss_ratio"] is not None:
            report_lines.append(f"- **Val / Train Loss Ratio**: {diagnostics['loss_ratio']:.2f}")

        if diagnostics["warnings"]:
            report_lines.append("\n### Diagnostic Warnings:")
            for w in diagnostics["warnings"]:
                report_lines.append(f"- {w}")
        else:
            report_lines.append("- No divergence detected. Loss reduction progressed steadily.")

        report_lines.extend([
            "",
            "## 4. Training Trajectory Table",
            "",
            "| Step | Train Loss | Val Loss | Val PPL | LR | Speed (tok/s) | Note |",
            "| :---: | :---: | :---: | :---: | :---: | :---: | :--- |",
        ])

        # Pick key logged steps for report table
        for m in self.metric_history:
            step = m["global_step"]
            t_loss = f"{m['train_loss']:.4f}" if m.get("train_loss") is not None else "N/A"
            v_loss = f"{m['val_loss']:.4f}" if m.get("val_loss") is not None else "-"
            v_ppl = f"{m.get('best_val_perplexity', 0.0):.2f}" if m.get("is_val_step") else "-"
            lr = f"{m['learning_rate']:.2e}"
            note = "Best Checkpoint" if m.get("is_best") else ("Validation" if m.get("is_val_step") else "")
            speed = f"{m.get('tokens_seen', 0) / max(1e-6, m.get('elapsed_seconds', 1)):,.0f}"
            report_lines.append(
                f"| {step} | {t_loss} | {v_loss} | {v_ppl} | {lr} | {speed} | {note} |"
            )

        with open(self.report_md_path, "w", encoding="utf-8") as f:
            f.write("\n".join(report_lines))

        logger.info(f"Experiment finalized. Report saved to {self.report_md_path}")
        return self.report_md_path
