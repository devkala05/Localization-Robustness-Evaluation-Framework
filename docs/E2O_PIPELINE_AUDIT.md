# Existing E2O pipeline audit

This is the pre-change implementation audit used to extend, rather than replace, the repository.

## Existing data and execution path

- E2O data is under `data/e2o`; the current `one_full_loop.bag` is played by `run.sh` from a ROS Noetic Docker container with `--clock`.
- `run.sh` owns the lifecycle: it starts a shared ROS master, the `localization_benchmark` input adapter, requested native estimator containers, health/recorder or fusion, optional RViz, and finally bag playback.
- Raw E2O topics are selected by environment variables and the adapter config. The adapter republishes estimator-native topics, camera information, preserved/scaled per-point time, and fault-injection streams.
- Calibration and frame transforms live in `wrappers/localization_benchmark/config/e2o.yaml`; `e2o_static_tf_publisher.py` publishes only the configured static transforms.
- FAST-LIVO2, ORB-SLAM3, and LVI-SAM are pinned and built in separate Docker images. External wrapper packages launch them and alias their native pose topics without changing estimator math.
- `multi_trajectory_recorder.py` writes the common timestamp/position/quaternion CSV schema and debug `Path` topics. Run logs and metadata are stored under `data/output/<run_id>`.
- RViz profiles are in `rviz/`; `run.sh` selects the estimator/fusion profile.
- `evaluation/evaluate.sh` and `evaluate_e2o.py` associate timestamps, apply the requested SE(3)/Sim(3) Umeyama alignment, and produce JSON/Markdown metrics and plots.

## Extension plan used

1. Add dataset metadata and streaming adapters while retaining the shared adapter, Docker lifecycle, CSV schema, and evaluator math.
2. Store public sequences below `data/datasets`, with resumable scripts and no duplicate extracted/generated bag.
3. Normalize both datasets to the existing estimator-facing ROS topics and `base_link` convention using only supplied calibration.
4. Add per-dataset native algorithm configs and a consistent `run_benchmark.sh` interface.
5. Convert official GNSS/INS ground truth independently, publish it for RViz, then validate each pair on a short interval before any complete run.
6. Preserve `run.sh` and all E2O defaults; re-run the existing unit/static validation after integration.
