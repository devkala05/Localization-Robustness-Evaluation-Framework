# Localization Robustness Evaluation Pipeline

This repository implements a Docker-based localization robustness evaluation scaffold for five SLAM/localization algorithms, KITTI-style multi-sensor sequences, perturbation scenarios, trajectory metrics, plots, resumable orchestration, and Gemini report generation.

## Quickstart

Prerequisites: Docker, Docker Compose v2, and NVIDIA Container Toolkit for GPU-enabled algorithm containers.

```bash
cp .env.example .env
./scripts/download_dataset.sh
docker compose --profile build build base
docker compose build orchestrator perturbation_injector evaluator
./scripts/run_pipeline.sh --algo fast_lio2 --scenario rain --sequence urban_01
```

The local command above uses deterministic synthetic trajectories so the evaluator, reports, plots, and resume behavior can be tested before downloading full datasets and building external SLAM repositories.

## Full Pipeline

```bash
docker compose --profile build build base
docker compose build
docker compose up orchestrator
```

A single run can be filtered:

```bash
./scripts/run_pipeline.sh --algo fast_lio2 --scenario baseline --sequence urban_01
./scripts/run_pipeline.sh --algo fast_lio2 --scenario rain --sequence urban_01
```

## Results

Scenario outputs are written to:

```text
results/scenarios/{algo}/{sequence}/{scenario}/
```

Each completed scenario contains:

- `trajectory.tum`
- `metrics.json`
- `deviation_report.txt`
- `plots/trajectory_comparison.png`
- `plots/error_vs_time.png`
- `plots/lateral_longitudinal_error.png`
- `plots/error_heatmap.png`
- `gemini_summary.txt`

Final outputs are written to `results/final_report/`.

## Gemini

Set `GEMINI_API_KEY` in `.env`. The configured model is `gemini-2.0-flash`, which is listed in Google AI documentation as the latest Gemini 2.0 Flash text model and has free-tier pricing information on the Gemini API pricing page.

Manual report generation:

```bash
python3 scripts/generate_report.py --mode scenario --metrics results/scenarios/fast_lio2/urban_01/rain/metrics.json
python3 scripts/generate_report.py --mode final
```

If the API key is not set, report files still get deterministic fallback summaries.
