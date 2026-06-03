from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml

from .metrics import evaluate


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--golden-tum", required=True)
    parser.add_argument("--run-tum", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--algorithm", required=True)
    parser.add_argument("--sequence", required=True)
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--perturbation-yaml", required=True)
    parser.add_argument("--config", default="config/pipeline.yaml")
    args = parser.parse_args()

    cfg = yaml.safe_load(Path(args.config).read_text()) if Path(args.config).exists() else {}
    eval_cfg = cfg.get("evaluation", {})
    out_cfg = cfg.get("output", {})
    perturbation_params = yaml.safe_load(Path(args.perturbation_yaml).read_text())
    metrics = evaluate(
        args.golden_tum,
        args.run_tum,
        args.output_dir,
        args.algorithm,
        args.sequence,
        args.scenario,
        perturbation_params,
        failure_threshold_m=float(eval_cfg.get("failure_threshold_m", 5.0)),
        tracking_loss_threshold_m=float(eval_cfg.get("tracking_loss_threshold_m", 10.0)),
        plot_dpi=int(out_cfg.get("plot_dpi", 150)),
    )
    print(json.dumps({"metrics": str(Path(args.output_dir) / "metrics.json"), "rmse": metrics["rmse"]}, indent=2))


if __name__ == "__main__":
    main()
