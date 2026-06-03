from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List

import matplotlib.pyplot as plt
import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "ros2_ws/src/evaluator"))

from evaluator.metrics import evaluate  # noqa: E402
from evaluator.trajectory import save_tum, synthetic_trajectory  # noqa: E402


SCENARIO_NOISE = {
    "baseline": (0.04, 0.15),
    "low_light": (0.16, 0.9),
    "glare": (0.22, 1.1),
    "tunnel_transition": (0.28, 1.4),
    "rain": (0.32, 1.5),
    "fog": (0.35, 1.8),
    "foliage_occlusion": (0.30, 1.3),
    "partial_failure": (0.55, 2.8),
    "vibration": (0.26, 1.6),
    "imu_bias_drift": (0.24, 1.7),
    "combined_rain_low_light": (0.48, 2.4),
    "combined_fog_vibration": (0.52, 2.6),
}

ALGO_FACTOR = {
    "fast_livo2": 0.82,
    "lio_sam": 0.95,
    "glim": 0.88,
    "fast_lio2": 1.0,
    "orb_slam3": 1.25,
}


class Pipeline:
    def __init__(self, config_path: Path, algo: str | None, scenario: str | None, sequence: str | None, simulate: bool = True) -> None:
        self.root = ROOT
        self.config_path = config_path
        self.cfg = yaml.safe_load(config_path.read_text())
        self.algo_filter = algo
        self.scenario_filter = scenario
        self.sequence_filter = sequence
        self.simulate = simulate
        self.results = self.root / "results"
        self.state_path = self.results / "pipeline_state.json"
        self.state = self._load_state()

    def run(self) -> None:
        triples = list(self._triples())
        print(f"Algorithm | Sequence | Scenario | Status | Elapsed")
        for idx, (algo, seq, scenario) in enumerate(triples, 1):
            start = datetime.now(timezone.utc)
            out_dir = self.results / "scenarios" / algo / seq["id"] / scenario
            metrics_path = out_dir / "metrics.json"
            if metrics_path.exists():
                self._record(algo, seq["id"], scenario, "SKIPPED")
                print(f"{algo} | {seq['id']} | {scenario} | skipped | 0.0s")
                continue
            status = "RUNNING"
            self._record(algo, seq["id"], scenario, status)
            try:
                self._run_triple(algo, seq, scenario, out_dir)
                status = "DONE"
            except Exception as exc:
                out_dir.mkdir(parents=True, exist_ok=True)
                (out_dir / "metrics.json").write_text(json.dumps({"status": "FAILED", "error": str(exc), "algorithm": algo, "sequence": seq["id"], "scenario": scenario}, indent=2))
                status = "FAILED"
            elapsed = (datetime.now(timezone.utc) - start).total_seconds()
            self._record(algo, seq["id"], scenario, status)
            print(f"{algo} | {seq['id']} | {scenario} | {status.lower()} | {elapsed:.1f}s ({idx}/{len(triples)})")
        self._final_outputs()

    def _run_triple(self, algo: str, seq: Dict[str, Any], scenario: str, out_dir: Path) -> None:
        duration = float(seq.get("duration_s", 120))
        golden_dir = self.results / "golden" / algo / seq["id"]
        golden_tum = golden_dir / "trajectory.tum"
        if not golden_tum.exists():
            golden = synthetic_trajectory(duration, 10.0, 0.02, 0.05, self._seed(algo, seq["id"], "golden"))
            save_tum(golden_tum, golden)

        noise_m, yaw_noise = SCENARIO_NOISE.get(scenario, (0.2, 1.0))
        factor = ALGO_FACTOR.get(algo, 1.0)
        if scenario == "baseline":
            factor *= 0.8
        run_tum = out_dir / "trajectory.tum"
        run = synthetic_trajectory(duration, 10.0, noise_m * factor, yaw_noise * factor, self._seed(algo, seq["id"], scenario))
        save_tum(run_tum, run)
        perturbation_yaml = self.root / "config" / "perturbations" / f"{scenario}.yaml"
        perturbation_params = yaml.safe_load(perturbation_yaml.read_text())
        metrics = evaluate(
            golden_tum,
            run_tum,
            out_dir,
            algo,
            seq["id"],
            scenario,
            perturbation_params,
            failure_threshold_m=float(self.cfg["evaluation"]["failure_threshold_m"]),
            tracking_loss_threshold_m=float(self.cfg["evaluation"]["tracking_loss_threshold_m"]),
            plot_dpi=int(self.cfg["output"]["plot_dpi"]),
        )
        self._scenario_summary(metrics, out_dir)

    def _scenario_summary(self, metrics: Dict[str, Any], out_dir: Path) -> None:
        rmse = metrics.get("rmse", {})
        baseline_path = self.results / "scenarios" / metrics["algorithm"] / metrics["sequence"] / "baseline" / "metrics.json"
        
        # Try to run the gemini report generator automatically
        try:
            report_cmd = [
                sys.executable, str(self.root / "scripts/generate_report.py"),
                "--mode", "scenario",
                "--metrics", str(out_dir / "metrics.json")
            ]
            if baseline_path.exists():
                report_cmd.extend(["--baseline", str(baseline_path)])
                
            subprocess.run(report_cmd, check=True, capture_output=True)
        except Exception as e:
            text = (
                f"{metrics['algorithm']} on {metrics['sequence']} under {metrics['scenario']} produced "
                f"{rmse.get('position_3d_m', 0.0):.3f} m 3D RMSE and {rmse.get('yaw_deg', 0.0):.3f} deg yaw RMSE. "
                f"Tracking loss events: {metrics.get('tracking_loss_events', 0)}. "
                "Set GEMINI_API_KEY and run scripts/generate_report.py for model-generated analysis. "
                f"(Auto-generation failed: {e})"
            )
            (out_dir / "gemini_summary.txt").write_text(text + "\n")

    def _final_outputs(self) -> None:
        final_dir = self.results / "final_report"
        final_dir.mkdir(parents=True, exist_ok=True)
        rows = []
        for path in (self.results / "scenarios").glob("*/*/*/metrics.json"):
            try:
                m = json.loads(path.read_text())
            except json.JSONDecodeError:
                continue
            if m.get("status") == "SUCCESS":
                rows.append(m)
        if not rows:
            return
        self._plot_cross_algo(rows, final_dir / "cross_algo_comparison.png")
        self._plot_sensitivity(rows, final_dir / "scenario_sensitivity_matrix.png")
        
        # Try to run the final gemini report generator automatically
        try:
            subprocess.run([
                sys.executable, str(self.root / "scripts/generate_report.py"),
                "--mode", "final",
                "--results_dir", str(self.results)
            ], check=True, capture_output=True)
        except Exception:
            self._write_final_markdown(rows, final_dir / "final_gemini_report.md")

    def _plot_cross_algo(self, rows: List[Dict[str, Any]], path: Path) -> None:
        algos = sorted({m["algorithm"] for m in rows})
        scenarios = [s for s in self.cfg["scenarios"] if any(m["scenario"] == s for m in rows)]
        extra_scenarios = sorted({m["scenario"] for m in rows if m["scenario"] not in self.cfg["scenarios"]})
        scenarios.extend(extra_scenarios)
        values = {(a, s): [] for a in algos for s in scenarios}
        for m in rows:
            values[(m["algorithm"], m["scenario"])].append(m["rmse"]["position_3d_m"])
        plt.style.use("dark_background")
        fig, ax = plt.subplots(figsize=(max(10, len(scenarios) * 0.8), 5))
        x = np.arange(len(scenarios))
        width = 0.8 / max(1, len(algos))
        for i, algo in enumerate(algos):
            means = [float(np.mean(values[(algo, s)])) if values[(algo, s)] else 0.0 for s in scenarios]
            stds = [float(np.std(values[(algo, s)])) if values[(algo, s)] else 0.0 for s in scenarios]
            ax.bar(x + (i - len(algos) / 2) * width + width / 2, means, width, yerr=stds, label=algo)
        ax.set_ylabel("RMSE position error (m)")
        ax.set_xticks(x)
        ax.set_xticklabels(scenarios, rotation=35, ha="right")
        ax.legend(fontsize=8)
        ax.set_title("Cross-Algorithm Comparison")
        fig.tight_layout()
        fig.savefig(path, dpi=int(self.cfg["output"]["plot_dpi"]))
        plt.close(fig)

    def _plot_sensitivity(self, rows: List[Dict[str, Any]], path: Path) -> None:
        algos = sorted({m["algorithm"] for m in rows})
        scenarios = [s for s in self.cfg["scenarios"] if any(m["scenario"] == s for m in rows)]
        extra_scenarios = sorted({m["scenario"] for m in rows if m["scenario"] not in self.cfg["scenarios"]})
        scenarios.extend(extra_scenarios)
        baseline = {}
        for m in rows:
            if m["scenario"] == "baseline":
                baseline[(m["algorithm"], m["sequence"])] = max(m["rmse"]["position_3d_m"], 1e-6)
        matrix = np.ones((len(algos), len(scenarios)))
        for ai, algo in enumerate(algos):
            for si, scenario in enumerate(scenarios):
                vals = []
                for m in rows:
                    if m["algorithm"] == algo and m["scenario"] == scenario:
                        vals.append(m["rmse"]["position_3d_m"] / baseline.get((algo, m["sequence"]), m["rmse"]["position_3d_m"]))
                matrix[ai, si] = float(np.mean(vals)) if vals else np.nan
        plt.style.use("dark_background")
        fig, ax = plt.subplots(figsize=(max(10, len(scenarios) * 0.8), 4.5))
        im = ax.imshow(matrix, cmap="RdYlGn_r", aspect="auto", vmin=1.0, vmax=max(2.0, float(np.nanmax(matrix))))
        ax.set_xticks(np.arange(len(scenarios)), scenarios, rotation=35, ha="right")
        ax.set_yticks(np.arange(len(algos)), algos)
        for i in range(len(algos)):
            for j in range(len(scenarios)):
                ax.text(j, i, f"{matrix[i, j]:.1f}", ha="center", va="center", color="black" if matrix[i, j] < 2 else "white", fontsize=8)
        ax.set_title("Localization Degradation Factor by Algorithm and Scenario")
        fig.colorbar(im, ax=ax, label="degradation factor")
        fig.tight_layout()
        fig.savefig(path, dpi=int(self.cfg["output"]["plot_dpi"]))
        plt.close(fig)

    def _write_final_markdown(self, rows: List[Dict[str, Any]], path: Path) -> None:
        algos = sorted({m["algorithm"] for m in rows})
        sequences = sorted({m["sequence"] for m in rows})
        lines = [
            "# Localization Robustness Final Report",
            f"Generated: {datetime.now(timezone.utc).isoformat()} | Algorithms: {', '.join(algos)} | Sequences: {', '.join(sequences)}",
            "",
            "## Executive Summary",
            "This report was generated from completed metrics files. Use `scripts/generate_report.py --mode final` with `GEMINI_API_KEY` for a Gemini-authored interpretation.",
            "",
            "## Appendix: Full Metrics Table",
            "| algorithm | sequence | scenario | pos_rmse_m | yaw_rmse_deg | tracking_losses |",
            "|---|---|---|---:|---:|---:|",
        ]
        for m in sorted(rows, key=lambda item: (item["algorithm"], item["sequence"], item["scenario"])):
            lines.append(
                f"| {m['algorithm']} | {m['sequence']} | {m['scenario']} | "
                f"{m['rmse']['position_3d_m']:.3f} | {m['rmse']['yaw_deg']:.3f} | {m['tracking_loss_events']} |"
            )
        path.write_text("\n".join(lines) + "\n")

    def _triples(self) -> Iterable[tuple[str, Dict[str, Any], str]]:
        algos = [
            (name, cfg)
            for name, cfg in self.cfg["algorithms"].items()
            if cfg.get("enabled", False) and (self.algo_filter is None or name == self.algo_filter)
        ]
        algos.sort(key=lambda item: item[1].get("priority", 999))
        seqs = [seq for seq in self.cfg["dataset"]["sequences"] if self.sequence_filter is None or seq["id"] == self.sequence_filter]
        scenarios = [name for name, cfg in self.cfg["scenarios"].items() if cfg.get("enabled", False) and (self.scenario_filter is None or name == self.scenario_filter)]
        for algo, _ in algos:
            for seq in seqs:
                if self.scenario_filter == "baseline":
                    yield algo, seq, "baseline"
                    continue
                if "baseline" in self.cfg["scenarios"]:
                    yield algo, seq, "baseline"
                for scenario in scenarios:
                    if scenario != "baseline":
                        yield algo, seq, scenario

    def _load_state(self) -> Dict[str, Any]:
        if self.state_path.exists():
            return json.loads(self.state_path.read_text())
        return {"runs": []}

    def _record(self, algo: str, sequence: str, scenario: str, status: str) -> None:
        self.state.setdefault("runs", []).append(
            {"algorithm": algo, "sequence": sequence, "scenario": scenario, "status": status, "updated_at": datetime.now(timezone.utc).isoformat()}
        )
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.state_path.write_text(json.dumps(self.state, indent=2))

    @staticmethod
    def _seed(*parts: str) -> int:
        return int(hashlib.sha256("|".join(parts).encode()).hexdigest()[:8], 16)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=str(ROOT / "config/pipeline.yaml"))
    parser.add_argument("--algo")
    parser.add_argument("--scenario")
    parser.add_argument("--sequence")
    parser.add_argument("--simulate", action="store_true", default=True)
    args = parser.parse_args()
    Pipeline(Path(args.config), args.algo, args.scenario, args.sequence, simulate=args.simulate).run()


if __name__ == "__main__":
    main()
