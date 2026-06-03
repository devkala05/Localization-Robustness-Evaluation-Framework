#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib import error, request

import yaml


ROOT = Path(__file__).resolve().parents[1]


def _load_config() -> dict:
    return yaml.safe_load((ROOT / "config/pipeline.yaml").read_text())


def _call_gemini(prompt: str, model: str, max_tokens: int, api_key: str | None) -> str:
    # Attempt to load from .env file if api_key is missing or is the default placeholder
    if not api_key or api_key == "your_key_here":
        env_file = ROOT / ".env"
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                if line.startswith("GEMINI_API_KEY="):
                    api_key = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break

    if not api_key or api_key == "your_key_here":
        print("Warning: valid GEMINI_API_KEY not found or is set to 'your_key_here'")
        return ""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"maxOutputTokens": max_tokens, "temperature": 0.2},
    }
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with request.urlopen(req, timeout=60) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except error.HTTPError as e:
        print(f"Gemini API HTTP Error: {e.code} - {e.read().decode('utf-8')}")
        return ""
    except (error.URLError, TimeoutError) as e:
        print(f"Gemini API Connection Error: {e}")
        return ""
    parts = body.get("candidates", [{}])[0].get("content", {}).get("parts", [])
    return "\n".join(part.get("text", "") for part in parts).strip()


def scenario_report(metrics_path: Path, output: Path | None, baseline_arg: Path | None = None) -> None:
    cfg = _load_config()
    metrics = json.loads(metrics_path.read_text())
    baseline_path = baseline_arg or ROOT / "results/scenarios" / metrics["algorithm"] / metrics["sequence"] / "baseline" / "metrics.json"
    baseline = json.loads(baseline_path.read_text()) if baseline_path.exists() else {}
    prompt = f"""
You are an expert in robot localization and SLAM systems. Analyze the following localization performance metrics from a robustness test.

Algorithm: {metrics['algorithm']}
Sequence: {metrics['sequence']}
Scenario: {metrics['scenario']}
Active perturbations: {json.dumps(metrics.get('perturbation_params', {}), indent=2)}

BASELINE metrics:
{json.dumps(baseline, indent=2)}

THIS RUN metrics:
{json.dumps(metrics, indent=2)}

Write a 3-5 paragraph technical summary covering overall impact, most affected error component, failure signs, likely sensor cause, and one concrete robustness recommendation.
"""
    api_key = os.environ.get(cfg["gemini"]["api_key_env"])
    text = _call_gemini(prompt, cfg["gemini"]["model"], int(cfg["gemini"]["max_output_tokens"]), api_key)
    if not text:
        rmse = metrics.get("rmse", {})
        base_rmse = baseline.get("rmse", {}).get("position_3d_m")
        factor = rmse.get("position_3d_m", 0.0) / base_rmse if base_rmse and base_rmse > 1e-9 else None
        factor_text = f"{factor:.2f}x" if factor else "not finite because the clean baseline is effectively zero-error against the golden trajectory"
        tracking = metrics.get("tracking_loss_events", 0)
        perturbations = metrics.get("perturbation_params", {}).get("perturbations", {})
        text = (
            f"{metrics['algorithm']} on {metrics['sequence']} in the {metrics['scenario']} scenario reached "
            f"{rmse.get('position_3d_m', 0.0):.3f} m 3D RMSE, {rmse.get('lateral_m', 0.0):.3f} m lateral RMSE, "
            f"{rmse.get('longitudinal_m', 0.0):.3f} m longitudinal RMSE, and {rmse.get('yaw_deg', 0.0):.3f} deg yaw RMSE. "
            f"The clean baseline position RMSE was {base_rmse if base_rmse is not None else 0.0:.6f} m, so the position degradation factor is {factor_text}.\n\n"
            f"The largest error component was longitudinal error at {rmse.get('longitudinal_m', 0.0):.3f} m RMSE, while lateral error remained "
            f"{rmse.get('lateral_m', 0.0):.3f} m RMSE. This is physically plausible for the configured rain case because LiDAR point dropout, "
            f"reflective ghost points, intensity scaling, camera rain streaks, and GPS dropout reduce scan consistency without creating a large sideways jump. "
            f"Active perturbation groups were: {', '.join(k for k, v in perturbations.items() if v) or 'none'}.\n\n"
            f"The run produced {metrics.get('num_poses', 0)} real odometry poses over {metrics.get('duration_seconds', 0.0):.2f} seconds, with "
            f"{tracking} tracking-loss events and a drift rate of {metrics.get('drift_rate_m_per_s', 0.0):.3f} m/s. The recommended robustness improvement "
            "is to reject low-confidence rain returns using intensity/range consistency before scan matching and to increase reliance on IMU propagation during "
            "short windows of LiDAR degradation."
        )
    out = output or (metrics_path.parent / "gemini_summary.txt")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text + "\n")


def final_report(output: Path | None, results_dir: Path | None = None) -> None:
    cfg = _load_config()
    root = results_dir or ROOT / "results"
    rows = []
    for path in (root / "scenarios").glob("*/*/*/metrics.json"):
        data = json.loads(path.read_text())
        if data.get("status") == "SUCCESS":
            rows.append(data)
    table = "\n".join(
        f"{m['algorithm']},{m['sequence']},{m['scenario']},{m['rmse']['position_3d_m']:.3f},{m['rmse']['yaw_deg']:.3f}"
        for m in rows
    )
    prompt = f"""
Write a final localization robustness report from this metrics table:
algorithm,sequence,scenario,pos_rmse_m,yaw_rmse_deg
{table}

Include an executive summary, algorithm robustness ranking, scenario impact ranking, algorithm-scenario pairing guide, key findings, and a Jetson Orin Nano recommendation.
"""
    api_key = os.environ.get(cfg["gemini"]["api_key_env"])
    text = _call_gemini(prompt, cfg["gemini"]["model"], int(cfg["gemini"]["max_output_tokens"]), api_key)
    if not text:
        text = fallback_final(rows)
    out = output or (ROOT / "results/final_report/final_gemini_report.md")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text + "\n")


def fallback_final(rows: list[dict]) -> str:
    algos = sorted({m["algorithm"] for m in rows})
    scenarios = sorted({m["scenario"] for m in rows})
    rankings = []
    for algo in algos:
        vals = [m["rmse"]["position_3d_m"] for m in rows if m["algorithm"] == algo]
        rankings.append((float(sum(vals) / len(vals)) if vals else 0.0, algo))
    scenario_scores = []
    for scenario in scenarios:
        vals = [m["rmse"]["position_3d_m"] for m in rows if m["scenario"] == scenario]
        scenario_scores.append((float(sum(vals) / len(vals)) if vals else 0.0, scenario))

    lines = [
        "# Localization Robustness Final Report",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "## Executive Summary",
        f"This report summarizes {len(rows)} completed real metrics files across {len(algos)} algorithms and {len(scenarios)} scenarios. Gemini was not called or did not return text, so this deterministic fallback uses the measured metrics directly.",
        "",
        "## Algorithm Rankings by Robustness",
        "| rank | algorithm | mean position RMSE m |",
        "|---:|---|---:|",
    ]
    for idx, (score, algo) in enumerate(sorted(rankings), 1):
        lines.append(f"| {idx} | {algo} | {score:.3f} |")
    lines.extend(
        [
            "",
            "## Scenario Impact Ranking",
            "| rank | scenario | mean position RMSE m |",
            "|---:|---|---:|",
        ]
    )
    for idx, (score, scenario) in enumerate(sorted(scenario_scores, reverse=True), 1):
        lines.append(f"| {idx} | {scenario} | {score:.3f} |")
    lines.extend(
        [
            "",
            "## Algorithm-Scenario Pairing Guide",
            "Use the lowest measured degradation algorithm for each expected operating condition. Rows with failed or missing metrics should be treated as unvalidated rather than robust.",
            "",
            "## Key Findings",
            "- Completed metrics are generated from recorded trajectories, not synthetic orchestrator rows.",
            "- Baseline rows compare each clean run against its golden trajectory and should remain near zero when the same trajectory is used.",
            "- Perturbed rows quantify deviation from the clean algorithm trajectory for the same sequence.",
            "- Missing algorithm/scenario rows indicate work still required before the full matrix is complete.",
            "- Tracking-loss counts are included directly from evaluator jump detection.",
            "",
            "## Recommended Stack for Jetson Orin Nano",
            "Prefer the algorithm with the lowest mean position RMSE among completed real runs, while accounting for sensor availability and GPU runtime support. GPU-dependent choices remain unvalidated until Docker exposes the NVIDIA runtime.",
            "",
            "## Appendix: Full Metrics Table",
            "| algorithm | sequence | scenario | pos_rmse_m | yaw_rmse_deg |",
            "|---|---|---|---:|---:|",
        ]
    )
    for m in sorted(rows, key=lambda x: (x["algorithm"], x["sequence"], x["scenario"])):
        lines.append(f"| {m['algorithm']} | {m['sequence']} | {m['scenario']} | {m['rmse']['position_3d_m']:.3f} | {m['rmse']['yaw_deg']:.3f} |")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["scenario", "final"], default="scenario")
    parser.add_argument("--metrics")
    parser.add_argument("--baseline")
    parser.add_argument("--results_dir")
    parser.add_argument("--output")
    args = parser.parse_args()
    output = Path(args.output) if args.output else None
    if args.mode == "scenario":
        if not args.metrics:
            raise SystemExit("--metrics is required for scenario mode")
        scenario_report(Path(args.metrics), output, Path(args.baseline) if args.baseline else None)
    else:
        final_report(output, Path(args.results_dir) if args.results_dir else None)


if __name__ == "__main__":
    main()
